package io.github.aemiroo.yetiboss;
import java.net.*;
import java.net.http.*;
import java.time.Duration;
import java.nio.file.*;
import java.util.*;
import java.security.MessageDigest;
import java.util.concurrent.*;
import java.util.logging.Logger;
/** Bounded background delivery. Never logs URLs, tokens or response bodies. */
final class BossWebhook implements AutoCloseable {
    private final Logger log;
    private final Path stateDirectory;
    private final ThreadPoolExecutor queue=new ThreadPoolExecutor(1,1,0,TimeUnit.SECONDS,new ArrayBlockingQueue<>(32),r->{Thread t=new Thread(r,"YetiBoss-webhook");t.setDaemon(true);return t;});
    private final HttpClient client=HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
    BossWebhook(Logger log,Path stateDirectory){this.log=log;this.stateDirectory=stateDirectory;}
    static URI endpoint(String url) {
        URI uri;
        try{uri=URI.create(url);}catch(RuntimeException ex){throw new IllegalArgumentException("Invalid Discord webhook URL");}
        if(!"https".equals(uri.getScheme())||uri.getUserInfo()!=null||uri.getPort()!=-1
            ||!("discord.com".equals(uri.getHost())||"discordapp.com".equals(uri.getHost()))
            ||uri.getPath()==null||!uri.getPath().matches("/api(?:/v[0-9]+)?/webhooks/[0-9]+/[A-Za-z0-9_-]+"))
            throw new IllegalArgumentException("Expected a Discord HTTPS webhook URL");
        return uri;
    }
    static String quote(String value) {
        StringBuilder s=new StringBuilder("\"");
        for(char c:value.toCharArray())switch(c){
            case '"' -> s.append("\\\"");case '\\' -> s.append("\\\\");case '\n' -> s.append("\\n");case '\r' -> s.append("\\r");case '\t' -> s.append("\\t");
            default -> {if(c<32)s.append(String.format("\\u%04x",(int)c));else s.append(c);}
        }
        return s.append('"').toString();
    }
    static String payload(String title,String message,int color) {
        if(title.length()>256)title=title.substring(0,256);
        if(message.length()>4096)message=message.substring(0,4096);
        return "{\"allowed_mentions\":{\"parse\":[]},\"embeds\":[{\"title\":"+quote(title)+",\"description\":"+quote(message)+",\"color\":"+color+"}]}";
    }
    void send(String url,String title,String message,int color) {
        URI uri=endpoint(url);String json=payload(title,message,color);
        try{queue.execute(()->deliver(uri,json));}catch(RejectedExecutionException ex){log.warning("Discord webhook queue full or shutting down; announcement dropped.");}
    }
    static URI messageEndpoint(URI uri,String id) {
        if(!id.matches("[0-9]+"))throw new IllegalArgumentException("Invalid webhook message ID");
        return URI.create(uri.getScheme()+"://"+uri.getAuthority()+uri.getPath()+"/messages/"+id+
            (uri.getRawQuery()==null?"":"?"+uri.getRawQuery()));
    }
    static URI waitEndpoint(URI uri) {
        String query=uri.getRawQuery();
        List<String> parameters=new ArrayList<>();
        if(query!=null)for(String part:query.split("&"))if(!part.startsWith("wait="))parameters.add(part);
        parameters.add("wait=true");
        return URI.create(uri.getScheme()+"://"+uri.getAuthority()+uri.getPath()+"?"+String.join("&",parameters));
    }
    static String messageId(String json) {
        int depth=0;
        for(int i=0;i<json.length();i++) {
            char c=json.charAt(i);
            if(c=='{'||c=='['){depth++;continue;}
            if(c=='}'||c==']'){depth--;continue;}
            if(c!='"')continue;
            int start=++i;
            while(i<json.length()) {if(json.charAt(i)=='\\'){i+=2;continue;}if(json.charAt(i)=='"')break;i++;}
            if(depth==1&&json.substring(start,i).equals("id")) {
                var matcher=java.util.regex.Pattern.compile("\\s*:\\s*\"([0-9]+)\"").matcher(json.substring(i+1));
                if(matcher.lookingAt())return matcher.group(1);
            }
        }
        return null;
    }
    private HttpResponse<String> request(URI uri,String json) throws InterruptedException {
        for(int attempt=0;attempt<3;attempt++)try {
            var builder=HttpRequest.newBuilder(uri).timeout(Duration.ofSeconds(10));
            if(json==null)builder.DELETE();
            else builder.header("Content-Type","application/json").POST(HttpRequest.BodyPublishers.ofString(json));
            var response=client.send(builder.build(),HttpResponse.BodyHandlers.ofString());int status=response.statusCode();
            if(status>=200&&status<300||json==null&&status==404)return response;
            if(status!=429&&status<500||attempt==2){log.warning("Discord webhook request failed (HTTP "+status+").");return null;}
            double seconds=status==429?response.headers().firstValue("Retry-After").map(BossWebhook::retryDelay).orElse(2.0):Math.pow(2,attempt);
            Thread.sleep((long)(Math.max(1,Math.min(30,seconds))*1000));
        } catch(InterruptedException ex){throw ex;}
        catch(Exception ex){if(attempt==2)log.warning("Discord webhook connection failed after retries.");}
        return null;
    }
    private void deliver(URI uri,String json) {
        try {
            var response=request(waitEndpoint(uri),json);
            if(response==null)return; // Preserve the previous message if delivery failed.
            String id=messageId(response.body());
            if(id==null){log.warning("Discord did not return a webhook message ID; previous message retained.");return;}
            Files.createDirectories(stateDirectory);
            String hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(uri.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            Path file=stateDirectory.resolve(hash+".properties");Properties state=new Properties();
            if(Files.exists(file))try(var in=Files.newInputStream(file)){state.load(in);}
            Set<String> pending=new LinkedHashSet<>();
            for(String old:state.getProperty("pending","").split(","))if(old.matches("[0-9]+"))pending.add(old);
            String old=state.getProperty("last","");if(old.matches("[0-9]+")&&!old.equals(id))pending.add(old);
            state.setProperty("last",id);state.setProperty("pending",String.join(",",pending));saveState(file,state);
            for(var iterator=pending.iterator();iterator.hasNext();) {
                String previous=iterator.next();
                if(request(messageEndpoint(uri,previous),null)!=null)iterator.remove();
            }
            state.setProperty("pending",String.join(",",pending));saveState(file,state);
        } catch(InterruptedException ex){Thread.currentThread().interrupt();}
        catch(Exception ex){log.warning("Cannot save or clean up the previous Discord webhook message.");}
    }
    private static void saveState(Path file,Properties state) throws java.io.IOException {
        Path temp=file.resolveSibling(file.getFileName()+".tmp");
        try(var out=Files.newOutputStream(temp)){state.store(out,"YetiBoss webhook message IDs");}
        try{Files.move(temp,file,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);}
        catch(AtomicMoveNotSupportedException ex){Files.move(temp,file,StandardCopyOption.REPLACE_EXISTING);}
    }
    private static double retryDelay(String s){try{return Double.parseDouble(s);}catch(NumberFormatException ex){return 2;}}
    public void close(){queue.shutdownNow();}
}
