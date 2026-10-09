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
}
