import React, { useCallback, useEffect, useRef, useState } from "react";
import { Card, Button } from "../../components/UI";
import { pendingOwnerApi } from "../../services/api";
import { getOwnerSignupErrorFriendly, getStripeIdentityErrorCodeMessage } from "../../utils/ownerSignupErrors";

interface Props {
  navigate: (v: string) => void;
  setLoading: (l: boolean) => void;
  notify: (t: "success" | "error", m: string) => void;
}

type ErrorState = { message: string; sessionId: string | null };

/** Landing page after Stripe Identity redirect. Confirm once then go to POA or show failure with Try again / Start over. */
export default function OnboardingIdentityComplete({ navigate, setLoading, notify }: Props) {
  const [status, setStatus] = useState<"confirming" | "success" | "error">("confirming");
  const [errorState, setErrorState] = useState<ErrorState>({ message: "", sessionId: null });
  const hasRunRef = useRef(false);

  const onSuccess = useCallback(() => {
    setStatus("success");
    notify("success", "Identity verified. Completing signup…");
    setLoading(false);
    setTimeout(() => navigate("onboarding/poa"), 1500);
  }, [navigate, notify, setLoading]);

  const onFailure = useCallback(
    (errMessage: string, sessionId: string | null, errorCode?: string) => {
      setStatus("error");
      const codeMessage = getStripeIdentityErrorCodeMessage(errorCode);
      const friendly = getOwnerSignupErrorFriendly(codeMessage ?? errMessage);
      setErrorState({ message: codeMessage ?? friendly.message, sessionId });
      notify("error", codeMessage ?? friendly.message);
      setLoading(false);
    },
    [notify, setLoading]
  );

  const handleTryAgain = useCallback(() => {
    const sid = errorState.sessionId;
    if (!sid) {
      notify("error", "No verification session. Please start verification again.");
      navigate("onboarding/identity");
      return;
    }
    setLoading(true);
    pendingOwnerApi
      .getIdentityRetryUrl(sid)
      .then((r) => {
        if (r.already_verified) {
          onSuccess();
          return;
        }
        if (r.url) {
          window.location.href = r.url;
          return;
        }
        notify("error", r.message ?? "Could not get retry link. Please start verification again.");
        navigate("onboarding/identity?new=1");
      })
      .catch((e) => {
        const msg = (e as Error)?.message ?? "";
        const needsNewSession =
          msg.toLowerCase().includes("no longer valid") ||
          msg.toLowerCase().includes("start verification again") ||
          msg.toLowerCase().includes("expired") ||
          msg.toLowerCase().includes("invalid or expired");
        if (needsNewSession) {
          notify("error", msg);
          navigate("onboarding/identity?new=1");
        } else {
          setErrorState((prev) => ({ ...prev, message: msg }));
          notify("error", msg);
        }
        setLoading(false);
      });
  }, [errorState.sessionId, navigate, notify, onSuccess, setLoading]);

  const doConfirm = useCallback(
    (sessionId: string) => {
      setLoading(true);
      pendingOwnerApi
        .confirmIdentity(sessionId)
        .then(onSuccess)
        .catch((e) => {
          const err = e as Error & { errorCode?: string; sessionId?: string };
          onFailure(err?.message ?? "Could not confirm identity.", err.sessionId ?? sessionId, err.errorCode);
        });
    },
    [onSuccess, onFailure, setLoading]
  );

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

    if (sid) {
      doConfirm(sid);
      return;
    }

    setLoading(true);
    pendingOwnerApi
      .getLatestIdentitySession()
      .then((r) => {
        doConfirm(r.verification_session_id);
      })
      .catch((e) => {
        onFailure((e as Error)?.message ?? "", null);
      });
  }, [doConfirm, onFailure, setLoading]);

  return (
    <div className="flex-grow flex flex-col items-center justify-center p-6">
      <Card className="max-w-lg w-full p-8 text-center">
        <h1 className="text-xl font-semibold text-gray-900 mb-2">Verify your identity</h1>
        {status === "confirming" && (
          <p className="text-gray-600">Confirming your identity…</p>
        )}
        {status === "success" && (
          <p className="text-green-700">Identity verified. Redirecting…</p>
        )}
        {status === "error" && (
          <>
            <p className="text-red-600 text-sm mb-4">{errorState.message}</p>
            <p className="text-slate-600 text-sm mb-6">You can try again or start over from signup.</p>
            <div className="flex flex-col gap-3">
              <Button onClick={handleTryAgain} className="w-full">
                Try again
              </Button>
              <button
                type="button"
                onClick={() => navigate("onboarding/identity?new=1")}
                className="text-sm text-slate-600 underline hover:text-slate-800"
              >
                Start verification again
              </button>
              <button
                type="button"
                onClick={() => navigate("register")}
                className="text-sm text-slate-500 underline hover:text-slate-700"
              >
                Back to owner signup
              </button>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
