import { useState } from "react";
import AppShell from "../components/AppShell";
import TextField from "../components/TextField";
import { Button, ErrorList } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import client from "../api/client";

export default function Profile() {
  const { user, updateUser } = useAuth();
  const [form, setForm] = useState({
    full_name: user?.full_name || "",
    company_name: user?.company_name || "",
  });
  const [errors, setErrors] = useState([]);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  const [pwForm, setPwForm] = useState({ current_password: "", new_password: "" });
  const [pwErrors, setPwErrors] = useState([]);
  const [pwSaved, setPwSaved] = useState(false);
  const [pwSaving, setPwSaving] = useState(false);

  const onProfileSubmit = async (e) => {
    e.preventDefault();
    setErrors([]);
    setSaved(false);
    setSaving(true);
    try {
      const { data } = await client.put("/profile", form);
      updateUser(data.user);
      setSaved(true);
    } catch (err) {
      setErrors(err.response?.data?.errors || ["Could not update profile."]);
    } finally {
      setSaving(false);
    }
  };

  const onPasswordSubmit = async (e) => {
    e.preventDefault();
    setPwErrors([]);
    setPwSaved(false);
    setPwSaving(true);
    try {
      await client.put("/profile/password", pwForm);
      setPwSaved(true);
      setPwForm({ current_password: "", new_password: "" });
    } catch (err) {
      setPwErrors(err.response?.data?.errors || ["Could not update password."]);
    } finally {
      setPwSaving(false);
    }
  };

  return (
    <AppShell title="Profile">
      <div className="max-w-md space-y-10">
        <section>
          <h2 className="font-display font-semibold text-ink mb-4">Account details</h2>
          <form onSubmit={onProfileSubmit} className="space-y-4">
            <ErrorList errors={errors} />
            {saved && <p className="text-signal text-sm">Profile updated.</p>}
            <TextField
              label="Full name"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              required
            />
            <TextField
              label="Company"
              value={form.company_name}
              onChange={(e) => setForm({ ...form, company_name: e.target.value })}
            />
            <TextField label="Email" value={user?.email} disabled className="opacity-60" />
            <Button type="submit" loading={saving} className="w-auto px-5">
              Save changes
            </Button>
          </form>
        </section>

        <section>
          <h2 className="font-display font-semibold text-ink mb-4">Change password</h2>
          <form onSubmit={onPasswordSubmit} className="space-y-4">
            <ErrorList errors={pwErrors} />
            {pwSaved && <p className="text-signal text-sm">Password updated.</p>}
            <TextField
              label="Current password"
              type="password"
              value={pwForm.current_password}
              onChange={(e) => setPwForm({ ...pwForm, current_password: e.target.value })}
              required
            />
            <TextField
              label="New password"
              type="password"
              value={pwForm.new_password}
              onChange={(e) => setPwForm({ ...pwForm, new_password: e.target.value })}
              required
            />
            <Button type="submit" loading={pwSaving} className="w-auto px-5">
              Update password
            </Button>
          </form>
        </section>
      </div>
    </AppShell>
  );
}
