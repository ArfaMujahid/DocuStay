import React, { useEffect, useState } from "react";
import { Card, Button } from "../../components/UI";
import { pendingOwnerApi } from "../../services/api";

interface Props {
  navigate: (v: string) => void;
  setLoading: (l: boolean) => void;
  notify: (t: "success" | "error", m: string) => void;
}

/** Landing page after Stripe Identity redirect. pending_id = new signup flow; else existing owner. Confirm then go to POA. */
export default function OnboardingIdentityComplete({ navigate, setLoading, notify }: Props) {
  const [status, setStatus] = useState<"confirming" | "success" | "error">("confirming");
  const [message, setMessage] = useState<string>("");

  useEffect(() => {
    const search = window.location.search;
    const hash = window.location.hash.replace(/^#/, "");
    const params = new URLSearchParams(search);
    const hashQuery = hash.includes("?") ? hash.split("?")[1] : hash.includes("&") ? hash.slice(hash.indexOf("&") + 1) : "";
    const hashParams = hashQuery ? new URLSearchParams(hashQuery) : null;
    const fullUrl = window.location.href;
    const fromHref = (fullUrl.match(/[?&]session_id=([^&?#]+)/) || [])[1];
    let sid: string | null =
      params.get("session_id") ||
      hashParams?.get("session_id") ||
      (fromHref ? decodeURIComponent(fromHref.replace(/%2F/g, "/")) : null) ||
      null;
    const pendingId = params.get("pending_id") || hashParams?.get("pending_id") || null;

    const onSuccess = () => {
      setStatus("success");
      notify("success", "Identity verified. Now sign the Master POA to complete signup.");
      setLoading(false);
      setTimeout(() => navigate("onboarding/poa"), 1500);
    };
    const doConfirm = (sessionId: string) => {
      setLoading(true);
      // This page is only used in pending-owner onboarding; always use pending-owner confirm (identityApi is for existing users and would 401).
      pendingOwnerApi
        .confirmIdentity(sessionId)
        .then(onSuccess)
        .catch((e) => {
          setStatus("error");
          setMessage((e as Error)?.message ?? "Could not confirm identity.");
          notify("error", (e as Error)?.message ?? "Could not confirm identity.");
          setLoading(false);
        });
    };

    if (sid) {
      doConfirm(sid);
      return;
    }

    // Stripe sometimes redirects without session_id in URL (e.g. test mode or hash-only). Use backend-stored session id for this pending owner.
    setLoading(true);
    pendingOwnerApi
      .getLatestIdentitySession()
      .then((r) => {
        doConfirm(r.verification_session_id);
      })
      .catch((e) => {
        setStatus("error");
        const msg = (e as Error)?.message ?? "";
        setMessage(
          msg.includes("No identity session") || msg.includes("404")
            ? "No verification session found. Please go back and start verification from the identity step, then complete it on Stripe."
            : msg || "No verification session ID in URL. Start verification from the identity step, then complete it on Stripe."
        );
        setLoading(false);
      });
  }, [navigate, notify, setLoading]);

  return (
    <div className="flex-grow flex flex-col items-center justify-center p-6">
      <Card className="max-w-lg w-full p-8 text-center">
        <h1 className="text-xl font-semibold text-gray-900 mb-2">Identity Verification</h1>
        {status === "confirming" && (
          <p className="text-gray-600">Confirming your identity…</p>
        )}
        {status === "success" && (
          <p className="text-green-700">Identity verified. Redirecting to sign Master POA…</p>
        )}
        {status === "error" && (
          <>
            <p className="text-red-600 text-sm mb-4">{message}</p>
            <Button onClick={() => navigate("onboarding/identity")} className="w-full">
              Start verification again
            </Button>
          </>
        )}
      </Card>
    </div>
  );
}
