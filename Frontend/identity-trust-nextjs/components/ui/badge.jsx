import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium", {
  variants: {
    variant: {
      default: "bg-primary/15 text-primary",
      secondary: "bg-secondary text-secondary-foreground",
      destructive: "bg-destructive/15 text-destructive",
      caution: "bg-caution/15 text-caution",
      outline: "border border-border text-foreground",
    },
  },
  defaultVariants: { variant: "default" },
});

function Badge({ className, variant, ...props }) {
  return <div className={cn(badgeVariants({ variant, className }))} {...props} />;
}

export { Badge, badgeVariants };
