import React, { useEffect, useRef, useState } from "react";
import { Card, Button } from "../../components/UI";
import { pendingOwnerApi } from "../../services/api";
import { getOwnerSignupErrorFriendly } from "../../utils/ownerSignupErrors";

interface Props {
  navigate: (v: string) => void;
  setLoading: (l: boolean) => void;
  notify: (t: "success" | "error", m: string) => void;
}

/** Landing page after Stripe Identity redirect. Confirm once then go to POA or show failure with option to go back to signup. */
export default function OnboardingIdentityComplete({ navigate, setLoading, notify }: Props) {
  const [status, setStatus] = useState<"confirming" | "success" | "error">("confirming");
  const [message, setMessage] = useState<string>("");
  const hasRunRef = useRef(false);

  useEffect(() => {
    if (hasRunRef.current) return;
    hasRunRef.current = true;

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

    const onSuccess = () => {
      setStatus("success");
      notify("success", "Identity verified. Now sign the Master POA to complete signup.");
      setLoading(false);
      setTimeout(() => navigate("onboarding/poa"), 1500);
    };
    const onFailure = (errMessage: string) => {
      setStatus("error");
      const friendly = getOwnerSignupErrorFriendly(errMessage);
      setMessage(friendly.message);
      notify("error", friendly.message);
      setLoading(false);
    };
    const doConfirm = (sessionId: string) => {
      setLoading(true);
      pendingOwnerApi
        .confirmIdentity(sessionId)
        .then(onSuccess)
        .catch((e) => {
          onFailure((e as Error)?.message ?? "Could not confirm identity.");
        });
    };

    if (sid) {
      doConfirm(sid);
      return;
    }

    // Stripe sometimes redirects without session_id in URL. Use backend-stored session id for this pending owner.
    setLoading(true);
    pendingOwnerApi
      .getLatestIdentitySession()
      .then((r) => {
        doConfirm(r.verification_session_id);
      })
      .catch((e) => {
        onFailure((e as Error)?.message ?? "");
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
            <p className="text-slate-600 text-sm mb-6">Please start over from registration.</p>
            <Button onClick={() => navigate("register")} className="w-full">
              Back to owner signup
            </Button>
          </>
        )}
      </Card>
    </div>
  );
}
