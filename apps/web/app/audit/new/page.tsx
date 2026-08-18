"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "convex/react";
import { Upload, Link2, Loader2, ArrowRight } from "lucide-react";
import { api } from "@/convex/_generated/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const MAX_FILE_BYTES = 10 * 1024 * 1024; // 10MB
const ACCEPTED_TYPES = ["image/png", "image/jpeg", "image/webp"];

export default function NewAuditPage() {
  const router = useRouter();
  const generateUploadUrl = useMutation(api.files.generateUploadUrl);
  const createAudit = useMutation(api.audits.create);

  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleFileChange(selected: File | null) {
    setError(null);
    if (!selected) {
      setFile(null);
      return;
    }
    // Uploaded files are a trust boundary -- reject the obvious bad cases
    // client-side for fast feedback. This is UX, not the real security
    // boundary; the pipeline that actually reads the file re-validates.
    if (!ACCEPTED_TYPES.includes(selected.type)) {
      setError("Please choose a PNG, JPEG, or WebP image.");
      return;
    }
    if (selected.size > MAX_FILE_BYTES) {
      setError("That file is over 10MB — please use a smaller screenshot.");
      return;
    }
    setFile(selected);
  }

  function isPlausibleHttpUrl(value: string): boolean {
    try {
      const parsed = new URL(value);
      return parsed.protocol === "http:" || parsed.protocol === "https:";
    } catch {
      return false;
    }
  }

  async function submitScreenshot() {
    if (!file) return;
    setSubmitting(true);
    setError(null);
    try {
      const uploadUrl = await generateUploadUrl();
      const res = await fetch(uploadUrl, {
        method: "POST",
        headers: { "Content-Type": file.type },
        body: file,
      });
      if (!res.ok) throw new Error("Upload failed. Please try again.");
      const { storageId } = await res.json();
      const auditId = await createAudit({
        sourceType: "screenshot",
        screenshotStorageId: storageId,
      });
      router.push(`/audit/${auditId}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
      setSubmitting(false);
    }
  }

  async function submitUrl() {
    if (!isPlausibleHttpUrl(url)) {
      setError("Enter a valid http(s) URL.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const auditId = await createAudit({ sourceType: "url", sourceUrl: url });
      router.push(`/audit/${auditId}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-xl flex-1 flex-col justify-center gap-(--space-lg) px-(--space-lg) py-(--space-2xl)">
      <div className="flex flex-col gap-(--space-xs) text-center">
        <h1 className="text-2xl font-semibold sm:text-3xl">Start a new audit</h1>
        <p className="text-muted-foreground">
          Upload a UI screenshot, or paste a URL and Aura will capture one.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Source</CardTitle>
          <CardDescription>Choose how to give Aura the UI to review.</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="screenshot">
            <TabsList className="w-full">
              <TabsTrigger value="screenshot" className="flex-1 cursor-pointer">
                <Upload className="size-4" />
                Screenshot
              </TabsTrigger>
              <TabsTrigger value="url" className="flex-1 cursor-pointer">
                <Link2 className="size-4" />
                URL
              </TabsTrigger>
            </TabsList>

            <TabsContent value="screenshot" className="mt-(--space-md) flex flex-col gap-(--space-md)">
              <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPTED_TYPES.join(",")}
                className="hidden"
                onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="flex cursor-pointer flex-col items-center justify-center gap-(--space-sm) rounded-(--radius-lg) border border-dashed border-border bg-muted/40 px-(--space-md) py-(--space-xl) text-center text-sm text-muted-foreground transition-colors hover:border-primary/60 hover:text-foreground"
              >
                <Upload className="size-5" />
                {file ? file.name : "Click to choose a screenshot (PNG, JPEG, or WebP, up to 10MB)"}
              </button>
              <Button
                onClick={submitScreenshot}
                disabled={!file || submitting}
                className="cursor-pointer"
              >
                {submitting ? <Loader2 className="size-4 animate-spin" /> : <ArrowRight className="size-4" />}
                Run audit
              </Button>
            </TabsContent>

            <TabsContent value="url" className="mt-(--space-md) flex flex-col gap-(--space-md)">
              <div className="flex flex-col gap-(--space-xs)">
                <Label htmlFor="audit-url">Page URL</Label>
                <Input
                  id="audit-url"
                  type="url"
                  placeholder="https://example.com"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                />
              </div>
              <Button onClick={submitUrl} disabled={!url || submitting} className="cursor-pointer">
                {submitting ? <Loader2 className="size-4 animate-spin" /> : <ArrowRight className="size-4" />}
                Run audit
              </Button>
            </TabsContent>
          </Tabs>

          {error && <p className="mt-(--space-sm) text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>
    </div>
  );
}
