"use client";

import { useState, useEffect, useRef } from "react";
import { ArrowUp, Square, Paperclip, X, FileText, FileCode } from "lucide-react";

export interface AttachedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  content: string;
  isText: boolean;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileIcon(filename: string) {
  if (filename.match(/\.(ts|tsx|js|jsx|py|sql|json|html|css|yaml|yml|sh|env)$/i)) {
    return <FileCode size={13} className="text-[color:var(--accent)] shrink-0" />;
  }
  return <FileText size={13} className="text-[color:var(--theme-accent)] shrink-0" />;
}

export default function InputBox({
  onSend,
  disabled,
  streaming = false,
  onStop,
}: {
  onSend: (message: string) => void;
  disabled?: boolean;
  streaming?: boolean;
  onStop?: () => void;
}) {
  const [value, setValue] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [attachmentError, setAttachmentError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const canSend = (value.trim().length > 0 || attachedFiles.length > 0) && !disabled && !streaming;

  useEffect(() => {
    if (!textareaRef.current) return;
    const element = textareaRef.current;
    element.style.height = "auto";
    element.style.height = `${Math.min(element.scrollHeight, 200)}px`;
  }, [value]);

  const processFiles = async (fileList: FileList | File[]) => {
    setAttachmentError(null);
    const files = Array.from(fileList);
    const newAttachments: AttachedFile[] = [];

    for (const file of files) {
      if (file.size > 20 * 1024 * 1024) {
        setAttachmentError("Files over 20 MB cannot be attached.");
        continue;
      }

      const isTextFile =
        file.type.startsWith("text/") ||
        Boolean(file.name.match(/\.(txt|md|markdown|py|js|ts|tsx|jsx|json|csv|sql|html|css|yaml|yml|sh|env|xml|log|rst)$/i));

      if (isTextFile) {
        try {
          const text = await file.text();
          newAttachments.push({
            id: `${file.name}-${Date.now()}-${Math.random()}`,
            name: file.name,
            size: file.size,
            type: file.type || "text/plain",
            content: text,
            isText: true,
          });
        } catch {
          setAttachmentError(`Could not read ${file.name}. Try another text file.`);
        }
      } else {
        setAttachmentError("Only text files can be read by Miryn right now.");
      }
    }

    if (newAttachments.length > 0) {
      setAttachedFiles((prev) => [...prev, ...newAttachments]);
    }
  };

  const removeFile = (id: string) => {
    setAttachedFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const handleSend = () => {
    const trimmed = value.trim();
    if ((!trimmed && attachedFiles.length === 0) || disabled || streaming) return;

    let fullMessage = trimmed;
    if (attachedFiles.length > 0) {
      const attachmentsBlock = attachedFiles
        .map((f) => {
          const ext = f.name.split(".").pop() || "txt";
          if (f.isText) {
            return `[Attached File: ${f.name} (${formatFileSize(f.size)})]\n\`\`\`${ext}\n${f.content}\n\`\`\``;
          }
          return `[Attached File: ${f.name} (${formatFileSize(f.size)})]`;
        })
        .join("\n\n");

      fullMessage = trimmed ? `${attachmentsBlock}\n\n${trimmed}` : attachmentsBlock;
    }

    onSend(fullMessage);
    setValue("");
    setAttachedFiles([]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="relative w-full max-w-3xl mx-auto">
      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".txt,.md,.markdown,.py,.js,.ts,.tsx,.jsx,.json,.csv,.sql,.html,.css,.yaml,.yml,.sh,.env,.xml,.log,.rst,text/*"
        className="hidden"
        onChange={(e) => {
          if (e.target.files && e.target.files.length > 0) {
            void processFiles(e.target.files);
          }
        }}
      />

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            void processFiles(e.dataTransfer.files);
          }
        }}
        className={`relative flex flex-col bg-[color:var(--theme-card)] rounded-[28px] border transition-all duration-200 ${
          isDragging
            ? "border-[color:var(--theme-accent)] bg-[color:var(--theme-card)] shadow-[0_0_25px_var(--accent-glow)]"
            : "border-[color:var(--theme-border)] focus-within:border-[color:var(--theme-border)]"
        }`}
      >
        {/* Drag Overlay */}
        {isDragging && (
          <div className="absolute inset-0 z-30 bg-[color:var(--theme-surface)]/90 border-2 border-dashed border-[color:var(--theme-accent)] rounded-[26px] flex items-center justify-center gap-2 backdrop-blur-sm pointer-events-none">
            <Paperclip size={16} className="text-[color:var(--theme-accent)] animate-bounce" />
            <span className="text-xs font-mono text-[color:var(--theme-accent)] uppercase tracking-wider font-semibold">
              Drop text files to attach
            </span>
          </div>
        )}

        {/* Attached Files Tray */}
        {attachedFiles.length > 0 && (
          <div className="flex flex-wrap gap-2 px-3.5 pt-3 pb-1 border-b border-[color:var(--theme-border)]">
            {attachedFiles.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-2 bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] rounded-xl px-2.5 py-1.5 text-xs text-[color:var(--theme-text)] transition-all group"
              >
                {getFileIcon(file.name)}
                <span className="font-mono text-[11.5px] truncate max-w-[140px] text-[color:var(--theme-text)]">
                  {file.name}
                </span>
                <span className="text-xs font-mono text-[color:var(--theme-dim)]">
                  {formatFileSize(file.size)}
                </span>
                <button
                  type="button"
                  onClick={() => removeFile(file.id)}
                  className="text-[color:var(--theme-dim)] hover:text-white transition-colors p-0.5"
                  title="Remove attachment"
                >
                  <X size={12} />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Input Textarea & Controls */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="relative flex items-end gap-2 p-2"
        >
          {/* Paperclip Button */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            className="mb-0.5 flex h-11 w-11 items-center justify-center rounded-full p-2 text-[color:var(--theme-dim)] transition-all shrink-0 hover:bg-[color:var(--theme-overlay)] hover:text-[color:var(--theme-text)]"
            title="Attach a text file"
            aria-label="Attach files"
          >
            <Paperclip size={18} />
          </button>

          <textarea
            ref={textareaRef}
            className="flex-1 bg-transparent border-none px-2 py-2 text-[15px] leading-relaxed placeholder:text-[color:var(--theme-dim)] focus:outline-none focus:ring-0 resize-none max-h-[200px] overflow-y-auto custom-scrollbar text-[color:var(--theme-text)] min-h-[44px]"
            placeholder="Message Miryn"
            aria-label="Message Miryn"
            value={value}
            rows={1}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            disabled={disabled}
          />

          <button
            type={streaming ? "button" : "submit"}
            onClick={streaming ? onStop : undefined}
            className={`mb-0.5 mr-0.5 flex h-11 w-11 items-center justify-center rounded-full p-2 transition-all shrink-0 ${
              canSend || streaming
                ? "bg-[color:var(--theme-accent)] text-[color:var(--theme-accent-contrast)] hover:opacity-90"
                : "bg-[color:var(--theme-overlay)] text-[color:var(--theme-dim)] cursor-not-allowed"
            }`}
            disabled={!canSend && !streaming}
            aria-label={streaming ? "Stop generating" : "Send message"}
          >
            {streaming ? <Square size={13} fill="currentColor" /> : <ArrowUp size={16} strokeWidth={2.5} />}
          </button>
        </form>
      </div>

      {attachmentError && <p role="alert" className="mt-2 px-2 text-xs text-[color:var(--theme-danger-text)]">{attachmentError}</p>}

      <div className="mt-2 text-center">
        <p className="text-[11px] text-[color:var(--theme-dim)]">
          Miryn can make mistakes. Check important information.
        </p>
      </div>
    </div>
  );
}
