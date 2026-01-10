import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { LinkIcon } from "lucide-react";

interface DataPlaceholderProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  actionHref?: string;
  className?: string;
  children?: React.ReactNode;
}

export function DataPlaceholder({
  title = "Data Not Available",
  description = "Connect an account to view this information",
  actionLabel = "Connect Account",
  actionHref = "/connections",
  className = "",
  children,
}: DataPlaceholderProps) {
  return (
    <div className={`relative ${className}`}>
      {children && (
        <div className="blur-sm pointer-events-none select-none opacity-50">
          {children}
        </div>
      )}
      <div className="absolute inset-0 flex flex-col items-center justify-center bg-background/80 backdrop-blur-sm rounded-lg">
        <div className="text-center p-6 max-w-sm">
          <LinkIcon className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
          <h3 className="font-semibold text-lg mb-2">{title}</h3>
          <p className="text-sm text-muted-foreground mb-4">{description}</p>
          <Link to={actionHref}>
            <Button variant="default" size="sm">
              <LinkIcon className="h-4 w-4 mr-2" />
              {actionLabel}
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
