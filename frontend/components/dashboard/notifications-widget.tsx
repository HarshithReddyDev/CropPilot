"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Bell, AlertTriangle, Info, CheckCircle, CheckCheck } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import type { DashboardData } from "@/lib/constants";

interface NotificationsWidgetProps {
  data: DashboardData["notifications"];
  className?: string;
}

const typeConfig = {
  alert: { icon: AlertTriangle, color: "text-red-500", bg: "bg-red-500/10" },
  warning: { icon: AlertTriangle, color: "text-amber-500", bg: "bg-amber-500/10" },
  info: { icon: Info, color: "text-blue-500", bg: "bg-blue-500/10" },
  success: { icon: CheckCircle, color: "text-green-500", bg: "bg-green-500/10" },
};

export function NotificationsWidget({ data, className }: NotificationsWidgetProps) {
  const [notifications, setNotifications] = useState(data);
  const unreadCount = notifications.filter((n) => !n.isRead).length;

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));
  };

  return (
    <div className={cn("glass-card p-5", className)}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bell className="h-5 w-5 text-primary" />
          <h3 className="font-semibold text-sm">Notifications</h3>
          {unreadCount > 0 && (
            <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-primary px-1.5 text-[10px] font-bold text-primary-foreground">
              {unreadCount}
            </span>
          )}
        </div>
        {unreadCount > 0 && (
          <Button variant="ghost" size="sm" className="h-7 text-xs gap-1" onClick={markAllRead}>
            <CheckCheck className="h-3.5 w-3.5" />
            Mark all read
          </Button>
        )}
      </div>

      <div className="space-y-2 max-h-[320px] overflow-y-auto scrollbar-hide">
        {notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <Bell className="h-10 w-10 mb-2 opacity-30" />
            <p className="text-sm">No notifications</p>
          </div>
        ) : (
          notifications.map((notif, i) => {
            const config = typeConfig[notif.type];
            const Icon = config.icon;
            return (
              <motion.div
                key={notif.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04, duration: 0.2 }}
                className={cn(
                  "flex items-start gap-3 rounded-lg border p-3 transition-colors",
                  notif.isRead
                    ? "border-border bg-transparent"
                    : "border-primary/20 bg-primary/5"
                )}
              >
                <div className={cn("flex h-8 w-8 items-center justify-center rounded-full shrink-0", config.bg)}>
                  <Icon className={cn("h-4 w-4", config.color)} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{notif.title}</span>
                    {!notif.isRead && (
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0" />
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                    {notif.body}
                  </p>
                  <span className="text-[10px] text-muted-foreground mt-1 block">
                    {notif.time}
                  </span>
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
}
