import type { JSX } from 'react';

export interface Issue {
  severity: 'error' | 'warning' | 'info';
  title: string;
  description?: string;
}

interface IssuesListProps {
  issues: Issue[];
  className?: string;
}

const severityStyles: Record<
  Issue['severity'],
  {
    badge: string;
    card: string;
    label: string;
  }
> = {
  error: {
    badge: 'bg-red-100 text-red-700 ring-red-200',
    card: 'border-red-200 bg-red-50/70',
    label: 'Error',
  },
  warning: {
    badge: 'bg-yellow-100 text-yellow-800 ring-yellow-200',
    card: 'border-yellow-200 bg-yellow-50/70',
    label: 'Warning',
  },
  info: {
    badge: 'bg-blue-100 text-blue-700 ring-blue-200',
    card: 'border-blue-200 bg-blue-50/70',
    label: 'Info',
  },
};

function joinClassNames(...classNames: Array<string | undefined>): string {
  return classNames.filter(Boolean).join(' ');
}

export function IssuesList({
  issues,
  className,
}: IssuesListProps): JSX.Element | null {
  if (issues.length === 0) {
    return null;
  }

  return (
    <section className={joinClassNames('space-y-3', className)}>
      <div className="space-y-1">
        <h2 className="text-lg font-semibold text-slate-900">Issues</h2>
        <p className="text-sm text-slate-600">
          Context analysis detected the following issues.
        </p>
      </div>

      <ul className="space-y-3">
        {issues.map((issue, index) => {
          const styles = severityStyles[issue.severity];

          return (
            <li
              key={`${issue.severity}-${issue.title}-${index}`}
              className={joinClassNames(
                'rounded-xl border p-4 shadow-sm',
                styles.card,
              )}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-1">
                  <h3 className="text-sm font-medium text-slate-900">
                    {issue.title}
                  </h3>
                  {issue.description ? (
                    <p className="text-sm leading-6 text-slate-700">
                      {issue.description}
                    </p>
                  ) : null}
                </div>

                <span
                  className={joinClassNames(
                    'inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset',
                    styles.badge,
                  )}
                >
                  {styles.label}
                </span>
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export default IssuesList;
