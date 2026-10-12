import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LoginPage from "@/app/login/page";
import LoginForm from "@/components/login/LoginForm";

// Next.js Image needs to be mocked in jest environment
jest.mock('next/image', () => ({
  __esModule: true,
  default: ({ src, alt }: { src: string; alt: string }) => <img src={src} alt={alt} />,
}));

jest.mock("next/navigation", () => ({
  usePathname: () => "/login",
  useRouter: () => ({ push: jest.fn() }),
  redirect: jest.fn(),
}));

describe("LoginPage", () => {
  it("renders login page without crashing", () => {
    render(<LoginPage />);
    expect(screen.getByRole("main")).toBeInTheDocument();
  });

  it("renders Chip Detector branding", () => {
    render(<LoginPage />);
    expect(screen.getByAltText(/chip detector logo/i)).toBeInTheDocument();
  });

  it("renders the Login heading", () => {
    render(<LoginPage />);
    expect(screen.getByRole("heading", { name: /login/i })).toBeInTheDocument();
  });

  it("renders email and password inputs", () => {
    render(<LoginPage />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
  });

  it("renders the Sign in button", () => {
    render(<LoginPage />);
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("renders Forgot Password link", () => {
    render(<LoginPage />);
    expect(screen.getByText(/forgot password/i)).toBeInTheDocument();
  });

  it("renders Register for free link", () => {
    render(<LoginPage />);
    expect(screen.getByText(/register for free/i)).toBeInTheDocument();
  });
});

describe("LoginForm – validation", () => {
  const user = userEvent.setup();

  it("shows error when submitting empty form", async () => {
    render(<LoginForm />);
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
    expect(await screen.findByText(/password is required/i)).toBeInTheDocument();
  });

  it("shows error for invalid email format", async () => {
    render(<LoginForm />);
    await user.type(screen.getByLabelText(/email/i), "not-an-email");
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    expect(
      await screen.findByText(/enter a valid email address/i)
    ).toBeInTheDocument();
  });

  it("shows error for short password", async () => {
    render(<LoginForm />);
    await user.type(screen.getByLabelText(/email/i), "user@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    expect(
      await screen.findByText(/password must be at least 6 characters/i)
    ).toBeInTheDocument();
  });

  it("clears email error when user starts typing", async () => {
    render(<LoginForm />);
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
    await user.type(screen.getByLabelText(/email/i), "a");
    expect(screen.queryByText(/email is required/i)).not.toBeInTheDocument();
  });

  it("toggles password visibility", async () => {
    render(<LoginForm />);
    const passwordInput = screen.getByLabelText(/^password$/i);
    expect(passwordInput).toHaveAttribute("type", "password");
    await user.click(screen.getByLabelText(/toggle password visibility/i));
    expect(passwordInput).toHaveAttribute("type", "text");
    await user.click(screen.getByLabelText(/toggle password visibility/i));
    expect(passwordInput).toHaveAttribute("type", "password");
  });

  it("disables submit button while loading", async () => {
    render(<LoginForm />);
    await user.type(screen.getByLabelText(/email/i), "user@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "password123");
    const btn = screen.getByRole("button", { name: /sign in/i });
    fireEvent.click(btn);
    await waitFor(() =>
      expect(btn).toHaveTextContent(/signing in/i)
    );
  });
});
