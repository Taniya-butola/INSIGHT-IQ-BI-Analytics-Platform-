import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../components/AuthLayout";
import TextField from "../components/TextField";
import { Button, ErrorList } from "../components/ui";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const { register, loading } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: "",
    company_name: "",
    email: "",
    password: "",
  });
  const [errors, setErrors] = useState([]);

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    setErrors([]);
    const result = await register(form);
    if (result.ok) {
      navigate("/dashboard");
    } else {
      setErrors(result.errors);
    }
  };

  return (
    <AuthLayout
      eyebrow="Get started"
      title="Create your INSIGHT IQ account"
      subtitle="Turn spreadsheets into a boardroom-ready view of your business."
    >
      <form onSubmit={onSubmit} className="space-y-4">
        <ErrorList errors={errors} />
        <TextField
          label="Full name"
          name="full_name"
          autoComplete="name"
          value={form.full_name}
          onChange={onChange}
          placeholder="Priya Sharma"
          required
        />
        <TextField
          label="Company (optional)"
          name="company_name"
          value={form.company_name}
          onChange={onChange}
          placeholder="Sharma Retail Pvt. Ltd."
        />
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
          autoComplete="new-password"
          value={form.password}
          onChange={onChange}
          placeholder="At least 8 characters"
          required
        />
        <p className="text-xs text-ink-muted -mt-2">
          Use 8+ characters with an uppercase letter, a lowercase letter, and a number.
        </p>
        <Button type="submit" loading={loading}>
          Create account
        </Button>
      </form>

      <p className="text-sm text-ink-muted mt-6">
        Already have an account?{" "}
        <Link to="/login" className="text-signal hover:underline">
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}
