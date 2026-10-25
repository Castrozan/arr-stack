const findLibraryServer = (servers, media) =>
  servers.find(
    (server) =>
      !server.is4k && media.serviceId != null && server.id === media.serviceId,
  ) ?? servers.find((server) => server.isDefault && !server.is4k);

const libraryForMedia = (media) => {
  const settings = (0, settings_1.getSettings)();
  const isMovie = media.mediaType === media_1.MediaType.MOVIE;
  const server = findLibraryServer(
    isMovie ? settings.radarr : settings.sonarr,
    media,
  );
  if (!server) {
    return undefined;
  }
  const LibraryService = isMovie ? radarr_1.default : sonarr_1.default;
  return {
    resource: isMovie ? "/movie" : "/series",
    exclusionParameter: isMovie
      ? "addImportExclusion"
      : "addImportListExclusion",
    isHeld: isMovie
      ? (item) => item.tmdbId === media.tmdbId
      : (item) =>
          (media.tvdbId && item.tvdbId === media.tvdbId) ||
          item.tmdbId === media.tmdbId,
    client: new LibraryService({
      apiKey: server.apiKey,
      url: LibraryService.buildUrl(server, "/api/v3"),
    }).axios,
  };
};

const removeHeldLibraryItemWithFiles = async (media) => {
  const library = libraryForMedia(media);
  if (!library) {
    return;
  }
  const { data: items } = await library.client.get(library.resource, {
    params:
      media.mediaType === media_1.MediaType.MOVIE
        ? { tmdbId: media.tmdbId }
        : {},
  });
  const heldItem = items.find(library.isHeld);
  if (!heldItem) {
    return;
  }
  await library.client.delete(`${library.resource}/${heldItem.id}`, {
    params: { deleteFiles: true, [library.exclusionParameter]: false },
  });
  logger_1.default.info(
    `Removed ${heldItem.title} and its files while clearing media data`,
    {
      label: "Media",
      mediaId: media.id,
    },
  );
};

const removeLibraryFilesBeforeClearingMedia = async (
  request,
  _response,
  next,
) => {
  try {
    const media = await (0, datasource_1.getRepository)(
      Media_1.default,
    ).findOne({
      where: { id: Number(request.params.id) },
    });
    if (media) {
      await removeHeldLibraryItemWithFiles(media);
    }
    next();
  } catch (error) {
    logger_1.default.error(
      "Failed to remove library files while clearing media data",
      {
        label: "Media",
        mediaId: request.params.id,
        errorMessage: error.message,
      },
    );
    next({
      status: 500,
      message: "Failed to remove the media files from Sonarr or Radarr.",
    });
  }
};

mediaRoutes.delete(
  "/:id",
  (0, auth_1.isAuthenticated)(permissions_1.Permission.MANAGE_REQUESTS),
  removeLibraryFilesBeforeClearingMedia,
);
mediaRoutes.stack.unshift(mediaRoutes.stack.pop());
