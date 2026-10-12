package io.github.aemiroo.yetiboss;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class BossWebhookTest {
 @Test void protectsEndpointAndEscapesMessages() {
  assertThrows(IllegalArgumentException.class,()->BossWebhook.endpoint("https://example.com/api/webhooks/1/token"));
  assertThrows(IllegalArgumentException.class,()->BossWebhook.endpoint("http://discord.com/api/webhooks/1/token"));
  assertEquals("discord.com",BossWebhook.endpoint("https://discord.com/api/webhooks/1/token").getHost());
  assertEquals("\"a\\\"b\\\\c\\n\"",BossWebhook.quote("a\"b\\c\n"));
  assertTrue(BossWebhook.payload("Spawn","@everyone",55).contains("\"parse\":[]"));
 }
 @Test void extractsOnlyMessageIdAndBuildsScopedEndpoints() {
  assertEquals("123",BossWebhook.messageId("{\"author\":{\"id\":\"999\"},\"id\":\"123\"}"));
  assertNull(BossWebhook.messageId("{\"author\":{\"id\":\"999\"}}"));
  var uri=BossWebhook.endpoint("https://discord.com/api/webhooks/1/token?thread_id=42&wait=false");
  assertTrue(BossWebhook.waitEndpoint(uri).toString().endsWith("thread_id=42&wait=true"));
  assertEquals("/api/webhooks/1/token/messages/123",BossWebhook.messageEndpoint(uri,"123").getPath());
  assertThrows(IllegalArgumentException.class,()->BossWebhook.messageEndpoint(uri,"../1"));
 }
}
