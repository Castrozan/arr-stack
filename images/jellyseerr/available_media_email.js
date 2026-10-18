const buildOriginalMessage = EmailAgent.prototype.buildMessage;

EmailAgent.prototype.buildMessage = function (...arguments_) {
  const message = buildOriginalMessage.apply(this, arguments_);
  if (arguments_[0] !== __1.Notification.MEDIA_AVAILABLE || !message) {
    return message;
  }
  message.locals.actionUrl = `${(process.env.JELLYFIN_PUBLIC_URL || "http://localhost:8096").replace(/\/+$/, "")}/web/#/home`;
  message.locals.actionLabel = "Watch in Jellyfin";
  return message;
};
