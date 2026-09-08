import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Card from "@/components/ui/Card";

describe("Button", () => {
  it("renders children", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: /click me/i })).toBeInTheDocument();
  });

  it("renders disabled state", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("calls onClick handler", async () => {
    const onClick = jest.fn();
    const user = userEvent.setup();
    render(<Button onClick={onClick}>Click</Button>);
    await user.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("does not call onClick when disabled", async () => {
    const onClick = jest.fn();
    const user = userEvent.setup();
    render(<Button disabled onClick={onClick}>Click</Button>);
    await user.click(screen.getByRole("button"));
    expect(onClick).not.toHaveBeenCalled();
  });

  it("applies fullWidth class", () => {
    render(<Button fullWidth>Full</Button>);
    expect(screen.getByRole("button")).toHaveClass("w-full");
  });
});

describe("Input", () => {
  it("renders with label", () => {
    render(<Input id="test" label="Email" />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  });

  it("renders error message", () => {
    render(<Input id="test" label="Email" error="Required" />);
    expect(screen.getByRole("alert")).toHaveTextContent("Required");
  });

  it("calls onChange handler", async () => {
    const onChange = jest.fn();
    const user = userEvent.setup();
    render(<Input id="test" label="Email" onChange={onChange} />);
    await user.type(screen.getByLabelText(/email/i), "a");
    expect(onChange).toHaveBeenCalled();
  });

  it("renders eye toggle for password type", () => {
    render(<Input id="pwd" label="Password" type="password" />);
    expect(screen.getByLabelText(/show password/i)).toBeInTheDocument();
  });
});

describe("Card", () => {
  it("renders children", () => {
    render(<Card>Content here</Card>);
    expect(screen.getByText("Content here")).toBeInTheDocument();
  });

  it("applies dark variant class by default", () => {
    render(<Card data-testid="card">x</Card>);
    expect(screen.getByTestId("card")).toHaveClass("bg-[#1a2035]");
  });

  it("applies light variant class", () => {
    render(<Card variant="light" data-testid="card">x</Card>);
    expect(screen.getByTestId("card")).toHaveClass("bg-white");
  });
});
