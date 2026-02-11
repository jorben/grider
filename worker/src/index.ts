import { Container, getContainer } from "@cloudflare/containers";
import { Hono } from "hono";

export class GriderContainer extends Container<Env> {
  defaultPort = 5000;
  sleepAfter = "30m";
  enableInternet = true;
  envVars = {
    FLASK_ENV: "production",
    FLASK_HOST: "0.0.0.0",
    FLASK_PORT: "5000",
    PORT: "5000",
    CORS_ORIGINS: "*",
    LOG_LEVEL: "INFO",
    LOG_TO_CONSOLE: "true",
    WORKERS: "2",
  };

  override onStart() {
    console.log("GriderContainer started");
  }
  override onStop() {
    console.log("GriderContainer stopped");
  }
  override onError(error: unknown) {
    console.error("GriderContainer error:", error);
  }
}

const app = new Hono<{ Bindings: Env }>();

app.all("/*", async (c) => {
  const container = getContainer(c.env.GRIDER_CONTAINER);
  return container.fetch(c.req.raw);
});

export default app;
