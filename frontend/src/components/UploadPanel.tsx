import { ChangeEvent, DragEvent, useState } from "react";
import { UploadCloud } from "lucide-react";

type Props = {
  isUploading: boolean;
  onUpload: (file: File) => void;
};

export function UploadPanel({ isUploading, onUpload }: Props) {
  const [isDragging, setIsDragging] = useState(false);

  function submitFile(file?: File) {
    if (file) onUpload(file);
  }

  function handleInput(event: ChangeEvent<HTMLInputElement>) {
    submitFile(event.target.files?.[0]);
    event.target.value = "";
  }

  function handleDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setIsDragging(false);
    submitFile(event.dataTransfer.files[0]);
  }

  return (
    <label
      className={`upload-panel ${isDragging ? "dragging" : ""}`}
      onDragOver={(event) => {
        event.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      <UploadCloud size={30} />
      <span>{isUploading ? "Uploading..." : "Upload dashcam video"}</span>
      <p>MP4, MOV, AVI, or another OpenCV-readable video.</p>
      <input type="file" accept="video/*" onChange={handleInput} disabled={isUploading} />
    </label>
  );
}
