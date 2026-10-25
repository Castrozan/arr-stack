const assert = require("node:assert/strict");
const { once } = require("node:events");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const { createRequire } = require("node:module");
const requireApplication = createRequire("/app/package.json");
const express = requireApplication("express");
const datasource = requireApplication("./dist/datasource");
const { getSettings } = requireApplication("./dist/lib/settings");
const mediaRoutes = requireApplication("./dist/routes/media").default;

const heldSeries = {
  id: 38,
  title: "Held Series",
  tvdbId: 477424,
  tmdbId: 321518,
};
const heldMovie = { id: 12, title: "Held Movie", tmdbId: 769 };
const libraryItems = {
  "/api/v3/series": [heldSeries],
  "/api/v3/movie": [heldMovie],
};
const libraryRequests = [];
let libraryUnavailable = false;

const mediaRecords = new Map();
const clearedMediaIds = [];
const findMedia = async ({ where }) => mediaRecords.get(where.id) ?? null;
datasource.getRepository = () => ({
  findOne: findMedia,
  findOneOrFail: async (query) => {
    const media = await findMedia(query);
    if (!media) {
      throw new Error("Media not found");
    }
    return media;
  },
  remove: async (media) => {
    clearedMediaIds.push(media.id);
    mediaRecords.delete(media.id);
  },
});

async function listen(server) {
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  return server.address().port;
}

async function main() {
  const libraryServer = http.createServer((request, response) => {
    const url = new URL(request.url, "http://library.invalid");
    assert.equal(url.searchParams.get("apikey"), "library-api-key");
    url.searchParams.delete("apikey");
    libraryRequests.push(`${request.method} ${url.pathname}${url.search}`);
    if (libraryUnavailable) {
      response.writeHead(503).end();
      return;
    }
    response.writeHead(200, { "content-type": "application/json" });
    response.end(
      request.method === "GET"
        ? JSON.stringify(libraryItems[url.pathname] ?? [])
        : "",
    );
  });
  const libraryPort = await listen(libraryServer);
  const librarySettings = (id, name) => ({
    id,
    name,
    hostname: "127.0.0.1",
    port: libraryPort,
    apiKey: "library-api-key",
    useSsl: false,
    baseUrl: "",
    isDefault: true,
    is4k: false,
  });
  const settings = getSettings();
  settings.sonarr = [librarySettings(0, "Sonarr")];
  settings.radarr = [librarySettings(0, "Radarr")];

  const application = express();
  application.use((request, _response, next) => {
    request.user = { hasPermission: () => true };
    next();
  });
  application.use("/media", mediaRoutes);
  application.use((error, _request, response, _next) => {
    response.status(error.status ?? 500).json({ message: error.message });
  });
  const applicationServer = http.createServer(application);
  const applicationPort = await listen(applicationServer);

  async function clearMedia(media) {
    mediaRecords.set(media.id, media);
    libraryRequests.length = 0;
    const response = await fetch(
      `http://127.0.0.1:${applicationPort}/media/${media.id}`,
      {
        method: "DELETE",
      },
    );
    return response.status;
  }

  assert.equal(
    await clearMedia({
      id: 1,
      mediaType: "tv",
      tmdbId: 321518,
      tvdbId: 477424,
      serviceId: null,
    }),
    204,
  );
  assert.ok(
    libraryRequests.includes(
      "DELETE /api/v3/series/38?deleteFiles=true&addImportListExclusion=false",
    ),
  );
  assert.ok(clearedMediaIds.includes(1));

  assert.equal(
    await clearMedia({ id: 2, mediaType: "movie", tmdbId: 769, serviceId: 0 }),
    204,
  );
  assert.ok(
    libraryRequests.includes(
      "DELETE /api/v3/movie/12?deleteFiles=true&addImportExclusion=false",
    ),
  );
  assert.ok(clearedMediaIds.includes(2));

  assert.equal(
    await clearMedia({ id: 3, mediaType: "tv", tmdbId: 1, tvdbId: 2 }),
    204,
  );
  assert.ok(!libraryRequests.some((request) => request.startsWith("DELETE")));
  assert.ok(clearedMediaIds.includes(3));

  libraryUnavailable = true;
  assert.equal(
    await clearMedia({
      id: 4,
      mediaType: "tv",
      tmdbId: 321518,
      tvdbId: 477424,
    }),
    500,
  );
  assert.ok(!clearedMediaIds.includes(4));

  applicationServer.close();
  libraryServer.close();
}

function filesBelow(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      return filesBelow(entryPath);
    }
    return entry.name.endsWith(".js") ? [entryPath] : [];
  });
}

const builtPages = filesBelow("/app/.next").map((file) =>
  fs.readFileSync(file, "utf8"),
);
assert.ok(
  !builtPages.some((page) =>
    page.includes("media information will be recreated"),
  ),
);
assert.ok(
  builtPages.some((page) =>
    page.includes("remove it from Sonarr or Radarr, including all files"),
  ),
);

main().then(
  () => process.exit(0),
  (error) => {
    console.error(error);
    process.exit(1);
  },
);
