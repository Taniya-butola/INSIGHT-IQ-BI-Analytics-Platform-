import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../components/AuthLayout";
import TextField from "../components/TextField";
import { Button, ErrorList } from "../components/ui";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login, loading } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState([]);

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    setErrors([]);
    const result = await login(form);
    if (result.ok) {
      navigate("/dashboard");
    } else {
      setErrors(result.errors);
    }
  };

  return (
    <AuthLayout
      eyebrow="Welcome back"
      title="Log in to your workspace"
      subtitle="Pick up where you left off with your retail data."
    >
      <form onSubmit={onSubmit} className="space-y-4">
        <ErrorList errors={errors} />
        <TextField
          label="Email"
          type="email"
          name="email"
          autoComplete="email"
          value={form.email}
          onChange={onChange}
          placeholder="you@company.com"
          required
        />
        <TextField
          label="Password"
          type="password"
          name="password"
          autoComplete="current-password"
          value={form.password}
          onChange={onChange}
          placeholder="••••••••"
          required
        />
        <Button type="submit" loading={loading}>
          Log in
        </Button>
      </form>

      <p className="text-sm text-ink-muted mt-6">
        New to INSIGHT IQ?{" "}
        <Link to="/register" className="text-signal hover:underline">
          Create an account
        </Link>
      </p>
    </AuthLayout>
  );
}
