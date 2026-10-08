"use client";

import { useState, useEffect, useRef } from "react";
import { ArrowUp, Loader2, Paperclip, X, FileText, FileCode, Image as ImageIcon } from "lucide-react";

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

function getFileIcon(filename: string, type: string) {
  if (type.startsWith("image/") || filename.match(/\.(png|jpe?g|webp|svg|gif)$/i)) {
    return <ImageIcon size={13} className="text-[color:var(--theme-accent)] shrink-0" />;
  }
  if (filename.match(/\.(ts|tsx|js|jsx|py|sql|json|html|css|yaml|yml|sh|env)$/i)) {
    return <FileCode size={13} className="text-[#2dd4bf] shrink-0" />;
  }
  return <FileText size={13} className="text-[color:var(--theme-accent)] shrink-0" />;
}

export default function InputBox({
  onSend,
  disabled,
}: {
  onSend: (message: string) => void;
  disabled?: boolean;
}) {
  const [value, setValue] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const canSend = (value.trim().length > 0 || attachedFiles.length > 0) && !disabled;

  useEffect(() => {
    if (!textareaRef.current) return;
    const element = textareaRef.current;
    element.style.height = "auto";
    element.style.height = `${Math.min(element.scrollHeight, 200)}px`;
  }, [value]);

  const processFiles = async (fileList: FileList | File[]) => {
    const files = Array.from(fileList);
    const newAttachments: AttachedFile[] = [];

    for (const file of files) {
      if (file.size > 20 * 1024 * 1024) {
        // Skip files > 20MB
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
          // If text reading fails, record metadata
          newAttachments.push({
            id: `${file.name}-${Date.now()}-${Math.random()}`,
            name: file.name,
            size: file.size,
            type: file.type || "application/octet-stream",
            content: `[File attached: ${file.name} (${formatFileSize(file.size)})]`,
            isText: false,
          });
        }
      } else {
        newAttachments.push({
          id: `${file.name}-${Date.now()}-${Math.random()}`,
          name: file.name,
          size: file.size,
          type: file.type || "application/octet-stream",
          content: `[Binary file attached: ${file.name} (${formatFileSize(file.size)})]`,
          isText: false,
        });
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
    if ((!trimmed && attachedFiles.length === 0) || disabled) return;

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
    <div className="relative w-full max-w-3xl mx-auto px-4 md:px-0">
      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
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
        className={`relative flex flex-col bg-[color:var(--theme-surface)] rounded-[26px] border transition-all duration-200 shadow-sm ${
          isDragging
            ? "border-[color:var(--theme-accent)] bg-[color:var(--theme-card)] shadow-[0_0_25px_rgba(214,145,85,0.15)]"
            : "border-[color:var(--theme-border)] focus-within:border-[color:var(--theme-border)]"
        }`}
      >
        {/* Drag Overlay */}
        {isDragging && (
          <div className="absolute inset-0 z-30 bg-[color:var(--theme-surface)]/90 border-2 border-dashed border-[color:var(--theme-accent)] rounded-[26px] flex items-center justify-center gap-2 backdrop-blur-sm pointer-events-none">
            <Paperclip size={16} className="text-[color:var(--theme-accent)] animate-bounce" />
            <span className="text-xs font-mono text-[color:var(--theme-accent)] uppercase tracking-wider font-semibold">
              Drop files to attach to Miryn
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
                {getFileIcon(file.name, file.type)}
                <span className="font-mono text-[11.5px] truncate max-w-[140px] text-[color:var(--theme-text)]">
                  {file.name}
                </span>
                <span className="text-[10px] font-mono text-[color:var(--theme-dim)]">
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
            className="p-2 mb-0.5 text-[color:var(--theme-dim)] hover:text-[color:var(--theme-text)] hover:bg-[color:var(--theme-overlay)] rounded-full transition-all shrink-0"
            title="Attach documents, code, or data files"
            aria-label="Attach files"
          >
            <Paperclip size={18} />
          </button>

          <textarea
            ref={textareaRef}
            className="flex-1 bg-transparent border-none px-2 py-2 text-[15px] leading-relaxed placeholder:text-[color:var(--theme-dim)] focus:outline-none focus:ring-0 resize-none max-h-[200px] overflow-y-auto custom-scrollbar text-[color:var(--theme-text)] min-h-[44px]"
            placeholder="Message Miryn or drop files..."
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
            type="submit"
            className={`p-2 mb-0.5 mr-0.5 rounded-full flex items-center justify-center transition-all h-8 w-8 shrink-0 ${
              canSend
                ? "bg-gradient-to-tr from-[color:var(--theme-accent)] to-[color:var(--theme-accent-strong)] text-[color:var(--theme-accent-contrast)] hover:brightness-105 shadow-[0_0_15px_rgba(214,145,85,0.25)] active:scale-95"
                : "bg-[color:var(--theme-overlay)] text-[color:var(--theme-dim)] cursor-not-allowed"
            }`}
            disabled={!canSend}
            aria-label="Send message"
          >
            {disabled ? <Loader2 size={16} className="animate-spin text-[color:var(--theme-accent)]" /> : <ArrowUp size={16} strokeWidth={2.5} />}
          </button>
        </form>
      </div>

      <div className="mt-2 text-center">
        <p className="text-[11px] font-mono tracking-tight text-[color:var(--theme-dim)]">
          Miryn v0.1 • 384-dim continuous memory • End-to-end Fernet encrypted
        </p>
      </div>
    </div>
  );
}
