import { useRef, useState } from "react";

import { ACCEPT, ALLOWED_TYPES, MAX_FILE_BYTES } from "../constants.js";

const MAX_MB = MAX_FILE_BYTES / (1024 * 1024);

/** Client-side hint only; the backend re-validates type and size (FR-02). */
export function validateFile(file) {
  if (!file) return "Pilih gambar terlebih dahulu.";
  const typeOk = ALLOWED_TYPES.includes(file.type) || /\.(jpe?g|png|webp)$/i.test(file.name);
  if (!typeOk) return "Format harus JPG, PNG, atau WEBP.";
  if (file.size > MAX_FILE_BYTES) return `Ukuran file maksimum ${MAX_MB} MB.`;
  return null;
}

export default function UploadDropzone({ file, onSelect, disabled }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  function handleFiles(files) {
    onSelect(files?.[0] ?? null);
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragging(false);
    if (disabled) return;
    handleFiles(event.dataTransfer?.files);
  }

  return (
    <div
      className={`dropzone${dragging ? " dropzone--active" : ""}${disabled ? " dropzone--disabled" : ""}`}
      onDragOver={(event) => {
        event.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      onKeyDown={(event) => {
        if ((event.key === "Enter" || event.key === " ") && !disabled) {
          event.preventDefault();
          inputRef.current?.click();
        }
      }}
      role="button"
      tabIndex={0}
      aria-label="Area unggah gambar: klik atau tarik file ke sini"
    >
      <input
        ref={inputRef}
        className="dropzone__input"
        type="file"
        accept={ACCEPT}
        aria-label="Pilih gambar"
        disabled={disabled}
        onChange={(event) => {
          handleFiles(event.target.files);
          event.target.value = "";
        }}
      />
      <p className="dropzone__title">
        {file ? file.name : "Tarik gambar ke sini atau klik untuk memilih"}
      </p>
      <p className="dropzone__hint">JPG, PNG, atau WEBP · maksimum {MAX_MB} MB</p>
    </div>
  );
}
