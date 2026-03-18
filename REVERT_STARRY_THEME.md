# Revert Starry / Cosmic Theme – Safe Approach

## Situation

- **Theme commit:** `239dd57` ("theme change of application-frontend") – 22 files.
- **Merge into main:** `5cf1b91` (PR #1).
- **Commit after merge:** `96e62d9` ("updated") – touches 14 files, including **6 of the same frontend files** as the theme (App.tsx, DashboardAlertsPanel, GuestDashboard, OwnerDashboard, Settings, TenantDashboard).

So we cannot simply `git revert -m 1 5cf1b91`, because that would also undo changes from `96e62d9` in those 6 files. The safe approach is to **revert only the theme-related files** to their pre-theme state (`9c6254d`), then fix up any non-theme changes from `96e62d9` if needed.

---

## Option A – Revert theme files to pre-theme (recommended)

This restores the 22 theme-touched files to how they were **before** the theme (`9c6254d`). The only change from `96e62d9` in those files that we checked is in `App.tsx` (hide Starfield on verify page); once the theme is gone there is no Starfield, so that change is not needed.

**Steps:**

1. **Fetch and create a revert branch from current main**
   ```powershell
   cd "e:\DocuStay\DocuStay"
   git fetch origin
   git checkout -b revert-starry-theme origin/main
   ```

2. **Restore every theme-changed file to pre-theme (9c6254d)**
   Run the commands in `scripts/revert-starry-theme.ps1` (see below), or run them manually.

3. **Remove the theme-only component**
   - Delete `frontend/components/StarField.tsx` (it was added in the theme commit).

4. **Test**
   - Run the app and verify: landing, login, dashboards (owner, guest, tenant), agreement modal, settings, help.

5. **If something from 96e62d9 is missing**
   - For each of the 6 overlapping files, run:  
     `git show 96e62d9 -- frontend/ path/to/file`
   - If you see a real feature/bugfix (not just styling), re-apply that change manually.

6. **Commit**
   ```powershell
   git add -A
   git status   # confirm only intended files
   git commit -m "Revert starry/cosmic theme – restore original frontend styling"
   ```

---

## Option B – Revert the merge (only if 96e62d9 has no needed frontend changes)

If you are sure that **all** frontend changes in `96e62d9` are theme-related or optional:

```powershell
git fetch origin
git checkout main
git pull origin main
git revert -m 1 5cf1b91
# Resolve conflicts if any; then:
git commit -m "Revert merge of starry theme (PR #1)"
```

This removes the entire theme merge. If `96e62d9` had non-theme edits in the same files, they will be reverted too, so only use this if that’s acceptable.

---

## Files to revert (to 9c6254d) for Option A

**Theme-only (not changed in 96e62d9):**

- frontend/components/AgreementSignModal.tsx  
- frontend/components/AuthCardLayout.tsx  
- frontend/components/HeroBackground.tsx  
- frontend/components/InvitationsTabContent.tsx  
- frontend/components/InviteRoleChoiceModal.tsx  
- frontend/components/ModeSwitcher.tsx  
- frontend/components/UI.tsx  
- frontend/index.css  
- frontend/pages/Auth/Login.tsx  
- frontend/pages/Auth/RegisterOwner.tsx  
- frontend/pages/Guest/SignAgreement.tsx  
- frontend/pages/Landing.tsx  
- frontend/pages/Support/HelpCenter.tsx  

**Overlapping with 96e62d9 (still restore from 9c6254d; re-apply 96e62d9 logic only if needed):**

- frontend/App.tsx  
- frontend/components/DashboardAlertsPanel.tsx  
- frontend/pages/Guest/GuestDashboard.tsx  
- frontend/pages/Owner/OwnerDashboard.tsx  
- frontend/pages/Settings/Settings.tsx  
- frontend/pages/Tenant/TenantDashboard.tsx  

**Added by theme (remove):**

- frontend/components/StarField.tsx  

**Lockfiles (optional – revert if you want to drop theme-only deps):**

- frontend/package-lock.json  
- package-lock.json  

---

## After reverting

- Push the new branch and open a PR into `main`, or merge locally and push `main`.
- If you later want the theme again, it remains in history (commit `239dd57`); you can cherry-pick or re-apply it on a new branch.
