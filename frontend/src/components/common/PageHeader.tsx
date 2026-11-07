import React from 'react';

interface PageHeaderProps {
  title: string;
  description?: string;
  badge?: React.ReactNode;
  action?: React.ReactNode;
  breadcrumbs?: string[];
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  badge,
  action,
  breadcrumbs,
}) => {
  return (
    <div className="mb-8 border-b border-[#DCE5DF] pb-6">
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="mb-2 text-xs font-medium text-[#64736F] flex items-center gap-1.5" aria-label="Breadcrumb">
          {breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={idx}>
              {idx > 0 && <span>/</span>}
              <span className={idx === breadcrumbs.length - 1 ? 'text-[#1C2B2A] font-semibold' : ''}>
                {crumb}
              </span>
            </React.Fragment>
          ))}
        </nav>
      )}

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#1C2B2A]">
              {title}
            </h1>
            {badge}
          </div>
          {description && (
            <p className="mt-1.5 text-sm sm:text-base text-[#52615E] max-w-3xl leading-relaxed">
              {description}
            </p>
          )}
        </div>

        {action && <div className="shrink-0 flex items-center gap-3">{action}</div>}
      </div>
    </div>
  );
};

