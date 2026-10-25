FROM fallenbagel/jellyseerr:2.7.3@sha256:4538137bc5af902dece165f2bf73776d9cf4eafb6dd714670724af8f3eb77764
COPY available_media_email.js /tmp/available_media_email.js
COPY request-progress.css /app/public/request-progress.css
COPY request_progress_stylesheet.js /tmp/request_progress_stylesheet.js
COPY clear_media_removes_library_files.js /tmp/clear_media_removes_library_files.js
COPY --chown=node:node test_available_media_email.cjs /tmp/test_available_media_email.cjs
COPY --chown=node:node test_request_progress_stylesheet.cjs /tmp/test_request_progress_stylesheet.cjs
COPY --chown=node:node test_clear_media_removes_library_files.cjs /tmp/test_clear_media_removes_library_files.cjs
RUN cat /tmp/available_media_email.js >> /app/dist/lib/notifications/agents/email.js \
    && printf '\n;\n' >> /app/.next/server/pages/_document.js \
    && cat /tmp/request_progress_stylesheet.js >> /app/.next/server/pages/_document.js \
    && sed -i 's/| View Media in #{applicationTitle}/| #{actionLabel || "View Media in " + applicationTitle}/' /app/dist/templates/email/media-request/html.pug \
    && cat /tmp/clear_media_removes_library_files.js >> /app/dist/routes/media.js \
    && grep -rlF 'media information will be recreated' /app/.next | xargs sed -i 's/including any requests\. If this item exists in your {mediaServerName} library, the media information will be recreated during the next scan\./including any requests, and remove it from Sonarr or Radarr, including all files./' \
    && mkdir -p /app/.next/cache \
    && chown -R node:node /app/config /app/.next/cache \
    && rm /tmp/available_media_email.js /tmp/request_progress_stylesheet.js /tmp/clear_media_removes_library_files.js
USER node
RUN node /tmp/test_available_media_email.cjs && rm /tmp/test_available_media_email.cjs
RUN node /tmp/test_request_progress_stylesheet.cjs && rm /tmp/test_request_progress_stylesheet.cjs
RUN node /tmp/test_clear_media_removes_library_files.cjs && rm /tmp/test_clear_media_removes_library_files.cjs
