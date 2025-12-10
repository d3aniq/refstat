export default {
  async fetch(request) {
    try {
      const url = new URL(request.url).searchParams.get("url");

      if (!url) {
        return new Response("Missing ?url=", { status: 400 });
      }

      // Hämta HTML från stats.innebandy.se
      const resp = await fetch(url, {
        headers: {
          "User-Agent": "Mozilla/5.0 RefStatLite/1.0"
        }
      });

      const body = await resp.text();

      return new Response(body, {
        status: 200,
        headers: {
          "Content-Type": "text/html; charset=utf-8",
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Headers": "*"
        }
      });

    } catch (err) {
      return new Response("Proxy error: " + err.toString(), { status: 500 });
    }
  }
}
