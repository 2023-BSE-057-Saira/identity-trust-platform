"use client";
import { useRef, useState } from "react";
import { Upload, FileCheck2 } from "lucide-react";

export default function FileField({ label, accept, onChange }) {
  const inputRef = useRef(null);
  const [fileName, setFileName] = useState(null);

  function handleChange(e) {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      onChange(file);
    }
  }

  return (
    <div>
      <label className="mb-1.5 block text-sm text-muted-foreground">{label}</label>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="flex w-full items-center gap-3 rounded-lg border border-dashed border-border bg-background px-4 py-3 text-left text-sm transition-colors hover:border-primary"
      >
        {fileName ? (
          <>
            <FileCheck2 className="h-4 w-4 shrink-0 text-primary" strokeWidth={1.75} />
            <span className="truncate text-foreground">{fileName}</span>
          </>
        ) : (
          <>
            <Upload className="h-4 w-4 shrink-0 text-muted-foreground" strokeWidth={1.75} />
            <span className="text-muted-foreground">Choose a file…</span>
          </>
        )}
      </button>
      <input ref={inputRef} type="file" accept={accept} onChange={handleChange} className="hidden" />
    </div>
  );
}
