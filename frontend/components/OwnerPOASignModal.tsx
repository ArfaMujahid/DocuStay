import React, { useEffect, useMemo, useState } from "react";
import { Button, Input, Modal } from "./UI";
import { ownerPoaApi, type OwnerPOADocResponse } from "../services/api";
import { getOwnerSignupErrorFriendly } from "../utils/ownerSignupErrors";

type AckKey = "read" | "temporary" | "vacate" | "electronic";

export default function OwnerPOASignModal(props: {
  open: boolean;
  ownerEmail: string;
  ownerFullName: string;
  onClose: () => void;
  onSigned: (signatureId: number) => void;
  notify: (t: "success" | "error", m: string) => void;
}) {
  const { open, ownerEmail, ownerFullName, onClose, onSigned, notify } = props;

  const [doc, setDoc] = useState<OwnerPOADocResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [signing, setSigning] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [signError, setSignError] = useState<string | null>(null);
  const [typedSignature, setTypedSignature] = useState(ownerFullName || "");
  const [acks, setAcks] = useState<Record<AckKey, boolean>>({
    read: false,
    temporary: false,
    vacate: false,
    electronic: false,
  });

  const allAcks = useMemo(() => Object.values(acks).every(Boolean), [acks]);

  useEffect(() => {
    if (!open) return;
    setTypedSignature(ownerFullName || "");
    setAcks({ read: false, temporary: false, vacate: false, electronic: false });
    setLoadError(null);
    setSignError(null);

    setLoading(true);
    ownerPoaApi
      .getDocument(ownerEmail?.trim() || undefined)
      .then((d) => { setDoc(d); setLoadError(null); })
      .catch((e) => {
        const friendly = getOwnerSignupErrorFriendly((e as Error)?.message ?? "Could not load Master POA document.");
        setLoadError(friendly.message);
        notify("error", friendly.message);
      })
      .finally(() => setLoading(false));
  }, [open, ownerEmail, ownerFullName, notify]);

  const handleSign = async () => {
    setSignError(null);
    if (!ownerEmail?.trim()) {
      const msg = "Enter your email first.";
      notify("error", msg);
      return;
    }
    if (!typedSignature?.trim()) {
      const msg = "Type your full legal name to sign.";
      notify("error", msg);
      return;
    }
    if (!doc) {
      const msg = "Document is not loaded yet. Please wait or try again.";
      notify("error", msg);
      return;
    }
    if (!allAcks) {
      const msg = "Please acknowledge all items to proceed.";
      notify("error", msg);
      return;
    }

    setSigning(true);
    try {
      const res = await ownerPoaApi.signWithDropbox({
        owner_email: ownerEmail.trim(),
        owner_full_name: ownerFullName?.trim() || typedSignature.trim(),
        typed_signature: typedSignature.trim(),
        acks,
        document_hash: doc.document_hash,
      });
      notify("success", "Master POA sent to Dropbox Sign. Check your email to complete signing; you can download the signed PDF in Settings after signing.");
      onSigned(res.signature_id);
      onClose();
    } catch (e) {
      const friendly = getOwnerSignupErrorFriendly((e as Error)?.message ?? "Could not sign Master POA.");
      setSignError(friendly.message);
      notify("error", friendly.message);
    } finally {
      setSigning(false);
    }
  };

  const shortTitle = doc?.title ?? "Master Power of Attorney (POA)";

  return (
    <Modal open={open} onClose={onClose} title={shortTitle} className="max-w-5xl">
      <div className="p-6 md:p-8 space-y-6 bg-slate-50/50">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="space-y-1">
            <p className="text-sm text-slate-600">
              This one-time document designates DocuStay as your Authorized Agent for all properties you add.
            </p>
            <p className="text-xs text-slate-500 italic">DocuStay is a legal technology platform, not a law firm.</p>
          </div>
          {doc?.document_id ? (
            <span className="text-xs text-slate-500 font-mono">{doc.document_id}</span>
          ) : null}
        </div>

        {doc?.already_signed && (
          <div className="rounded-xl bg-emerald-50 border border-emerald-200 px-4 py-3 flex flex-wrap items-center gap-3">
            <span className="text-emerald-700 font-bold">✓ Signed</span>
            <span className="text-slate-600 text-sm">
              {doc.signed_by} on {doc.signed_at ? new Date(doc.signed_at).toLocaleDateString() : ""}
            </span>
            <Button
              onClick={() => doc?.signature_id != null && onSigned(doc.signature_id)}
              disabled={doc?.signature_id == null}
            >
              Use this signature and complete signup
            </Button>
          </div>
        )}

        {loadError && (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm" role="alert">
            {loadError}
          </div>
        )}
        {signError && (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm" role="alert">
            {signError}
          </div>
        )}
        <div className="grid lg:grid-cols-5 gap-6">
          <div className="lg:col-span-3">
            <div className="border border-slate-200 rounded-xl bg-white overflow-hidden shadow-sm">
              <div className="px-4 py-3 border-b border-slate-200">
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Master POA</p>
              </div>
              <div className="p-4 max-h-[50vh] overflow-y-auto whitespace-pre-wrap text-sm text-slate-700 leading-relaxed">
                {loading ? "Loading document…" : (doc?.content ?? "Document unavailable.")}
              </div>
            </div>
          </div>

          <div className="lg:col-span-2 space-y-4">
            <div className="border border-slate-200 rounded-xl bg-white p-5 space-y-4 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Acknowledgments</p>
              {(
                [
                  ["read", "I have read the entire Master POA"],
                  ["temporary", "I acknowledge this is a one-time account-level authorization"],
                  ["vacate", "I understand this covers all properties I add now and in the future"],
                  ["electronic", "I consent to electronic signature"],
                ] as Array<[AckKey, string]>
              ).map(([key, label]) => (
                <label key={key} className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={acks[key]}
                    onChange={(e) => setAcks((p) => ({ ...p, [key]: e.target.checked }))}
                    className="mt-0.5 w-5 h-5 rounded border-slate-300 bg-white text-blue-600 focus:ring-blue-500 shrink-0"
                  />
                  <span className="text-sm text-slate-700">{label}</span>
                </label>
              ))}
            </div>

            <div className="border border-slate-200 rounded-xl bg-white p-5 space-y-4 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Signature</p>
              {doc?.already_signed ? (
                <p className="text-sm text-slate-600">This document is already signed. You can close this window and continue registration.</p>
              ) : (
                <>
                  <Input
                    label="Type full legal name *"
                    name="typed_signature"
                    value={typedSignature}
                    onChange={(e) => setTypedSignature(e.target.value)}
                    placeholder="First Last"
                    required
                  />
                  <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold">
                    By signing, you agree this is legally binding.
                  </p>
                  <div className="flex flex-col gap-3 pt-1">
                    <div className="flex gap-3">
                      <Button variant="outline" onClick={onClose} className="flex-1 py-3">
                        Cancel
                      </Button>
                      <Button onClick={handleSign} disabled={signing || loading} className="flex-1 py-3">
                        {signing ? "Sending…" : "Sign with Dropbox Sign"}
                      </Button>
                    </div>
                    <p className="text-xs text-slate-500 leading-relaxed">
                      You will receive an email from Dropbox Sign with a link to sign. After signing there, you can download the signed PDF in Settings.
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
}
