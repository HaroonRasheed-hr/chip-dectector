import { render, screen } from "@testing-library/react";
import Navbar from "@/components/layout/Navbar";

jest.mock("next/navigation", () => ({
  usePathname: () => "/detection",
}));

describe("Navbar", () => {
  it("renders the banner landmark", () => {
    render(<Navbar />);
    expect(screen.getByRole("banner")).toBeInTheDocument();
  });

  it("renders the Chip Detector logo link", () => {
    render(<Navbar />);
    expect(screen.getByRole("link", { name: /chip detector home/i })).toBeInTheDocument();
  });

  it("renders App navigation link", () => {
    render(<Navbar />);
    expect(screen.getByRole("link", { name: /app/i })).toBeInTheDocument();
  });

  it("renders Files navigation link", () => {
    render(<Navbar />);
    expect(screen.getByRole("link", { name: /files/i })).toBeInTheDocument();
  });

  it("renders Community navigation link", () => {
    render(<Navbar />);
    expect(screen.getByRole("link", { name: /community/i })).toBeInTheDocument();
  });

  it("highlights the active route", () => {
    render(<Navbar />);
    const appLink = screen.getByRole("link", { name: /app/i });
    expect(appLink).toHaveClass("text-white");
  });
});
