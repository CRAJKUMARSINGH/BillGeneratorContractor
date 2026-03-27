import React from "react";

interface PrintStylesProps {
  orientation: "portrait" | "landscape";
  marginMm?: number;
}

/**
 * Injects a <style> block dynamically to control the printed page size and margins.
 * CRITICAL for PWD Document specifications.
 */
export function PrintStyles({ orientation, marginMm = 10 }: PrintStylesProps) {
  return (
    <style dangerouslySetInnerHTML={{ __html: `
      @media print {
        @page {
          size: A4 ${orientation};
          margin: ${marginMm}mm;
        }
      }
    `}} />
  );
}
