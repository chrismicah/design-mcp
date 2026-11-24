import React, { type ReactNode } from 'react';

interface MaintenanceDisclosureProps {
  /** Question shown in the disclosure control. */
  label: string;
  /** Optional details shown after the disclosure opens. */
  children: ReactNode;
}

/** Reveals maintenance escalation instructions. */
export function MaintenanceDisclosure({ label, children }: MaintenanceDisclosureProps) {
  return (
    <details>
      <summary>{label}</summary>
      {children}
    </details>
  );
}
