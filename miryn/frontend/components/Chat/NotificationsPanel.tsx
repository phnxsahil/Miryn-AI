"use client";

import type { Notification } from "@/lib/types";

type Props = {
  notifications: Notification[];
  onMarkRead: (id: string) => void;
};

/**
 * Render a compact notifications panel that lists provided notifications and exposes a "Mark read" action for new items.
 *
 * @param notifications - Array of notification objects to display; each item should include `id`, `type`, and optional `payload.message` and `status`.
 * @param onMarkRead - Callback invoked with a notification `id` when the "Mark read" button is clicked for a notification with status `"new"`.
 * @returns The panel element containing notification entries when `notifications` is non-empty, or `null` when there are no notifications.
 */
export default function NotificationsPanel({ notifications, onMarkRead }: Props) {
  if (!notifications.length) {
    return null;
  }

  return (
    <div className="border-t border-white/10 bg-black/40 px-6 py-4">
      <div className="text-xs uppercase tracking-[0.25em] text-secondary">Notifications</div>
      <div className="mt-3 space-y-2">
        {notifications.map((note) => (
          <div key={note.id} className="flex items-center justify-between gap-4 rounded border border-white/10 bg-white/5 px-3 py-2">
            <div className="text-xs text-white/80">{note.payload?.message || note.type}</div>
            {note.status === "new" && (
              <button
                className="text-[10px] uppercase tracking-[0.2em] text-amber-200 hover:text-amber-100"
                onClick={() => onMarkRead(note.id)}
              >
                Mark read
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
