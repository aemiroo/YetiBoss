package io.github.aemiroo.yetiboss;
import java.net.*;
import java.net.http.*;
import java.time.Duration;
import java.util.concurrent.*;
import java.util.logging.Logger;
/** Bounded background delivery. Never logs URLs, tokens or response bodies. */
final class BossWebhook implements AutoCloseable {
    private final Logger log;
    private final ThreadPoolExecutor queue=new ThreadPoolExecutor(1,1,0,TimeUnit.SECONDS,new ArrayBlockingQueue<>(32),r->{Thread t=new Thread(r,"YetiBoss-webhook");t.setDaemon(true);return t;});
    private final HttpClient client=HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
    BossWebhook(Logger log){this.log=log;}
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
    private void deliver(URI uri,String json) {
        for(int attempt=0;attempt<3;attempt++)try {
            var request=HttpRequest.newBuilder(uri).timeout(Duration.ofSeconds(10)).header("Content-Type","application/json").POST(HttpRequest.BodyPublishers.ofString(json)).build();
            var response=client.send(request,HttpResponse.BodyHandlers.discarding());int status=response.statusCode();
            if(status>=200&&status<300)return;
            if(status!=429&&status<500){log.warning("Discord webhook rejected an announcement (HTTP "+status+").");return;}
            if(attempt==2){log.warning("Discord webhook delivery failed after retries (HTTP "+status+").");return;}
            double seconds=status==429?response.headers().firstValue("Retry-After").map(BossWebhook::retryDelay).orElse(2.0):Math.pow(2,attempt);
            Thread.sleep((long)(Math.max(1,Math.min(30,seconds))*1000));
        } catch(InterruptedException ex){Thread.currentThread().interrupt();return;}
        catch(Exception ex){if(attempt==2)log.warning("Discord webhook connection failed after retries.");}
    }
    private static double retryDelay(String s){try{return Double.parseDouble(s);}catch(NumberFormatException ex){return 2;}}
    public void close(){queue.shutdownNow();}
}
