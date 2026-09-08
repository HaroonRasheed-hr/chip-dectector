import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import DetectionClient from "@/app/detection/DetectionClient";
import ModelSelector from "@/components/detection/ModelSelector";
import ExampleImages from "@/components/detection/ExampleImages";
import HowToUse from "@/components/detection/HowToUse";
import ShareBar from "@/components/detection/ShareBar";

jest.mock("next/image", () => ({
  __esModule: true,
  default: (props: React.ImgHTMLAttributes<HTMLImageElement>) => {
    // eslint-disable-next-line @next/next/no-img-element
    return <img {...props} alt={props.alt ?? ""} />;
  },
}));

jest.mock("next/navigation", () => ({
  usePathname: () => "/detection",
  useRouter: () => ({ push: jest.fn() }),
}));

// Mock URL.createObjectURL
global.URL.createObjectURL = jest.fn(() => "blob:mock-url");
global.URL.revokeObjectURL = jest.fn();

describe("DetectionClient (full page)", () => {
  it("renders the navbar", () => {
    render(<DetectionClient />);
    expect(screen.getByRole("banner")).toBeInTheDocument();
  });

  it("renders the main content area", () => {
    render(<DetectionClient />);
    expect(screen.getByRole("main")).toBeInTheDocument();
  });

  it("renders the How to Use section", () => {
    render(<DetectionClient />);
    expect(screen.getByText(/how to use/i)).toBeInTheDocument();
  });

  it("renders Model name section", () => {
    render(<DetectionClient />);
    expect(screen.getByText(/model name/i)).toBeInTheDocument();
  });

  it("Infer button is disabled initially (no image selected)", () => {
    render(<DetectionClient />);
    expect(
      screen.getByRole("button", { name: /run inference/i })
    ).toBeDisabled();
  });

  it("Infer button becomes enabled after selecting an example", async () => {
    const user = userEvent.setup();
    render(<DetectionClient />);
    const firstExample = screen.getAllByRole("option")[0];
    await user.click(firstExample);
    expect(
      screen.getByRole("button", { name: /run inference/i })
    ).not.toBeDisabled();
  });

  it("shows inferring state when Infer is clicked", async () => {
    const user = userEvent.setup();
    render(<DetectionClient />);
    await user.click(screen.getAllByRole("option")[0]);
    const inferBtn = screen.getByRole("button", { name: /run inference/i });
    fireEvent.click(inferBtn);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /run inference/i })).toHaveTextContent(/inferring/i)
    );
  });
});

describe("ModelSelector", () => {
  const onChange = jest.fn();

  it("renders all three model options", () => {
    render(
      <ModelSelector selected="detr-resnet-50" onChange={onChange} />
    );
    const options = screen.getAllByRole("radio");
    expect(options).toHaveLength(3);
  });

  it("marks the selected model as checked", () => {
    render(
      <ModelSelector selected="detr-resnet-101" onChange={onChange} />
    );
    const resnet101 = screen.getByRole("radio", { name: /detr-resnet-101/i });
    expect(resnet101).toHaveAttribute("aria-checked", "true");
  });

  it("calls onChange when a model is clicked", async () => {
    const user = userEvent.setup();
    render(
      <ModelSelector selected="detr-resnet-50" onChange={onChange} />
    );
    const resnet101 = screen.getByRole("radio", { name: /detr-resnet-101/i });
    await user.click(resnet101);
    expect(onChange).toHaveBeenCalledWith("detr-resnet-101");
  });
});

describe("ExampleImages", () => {
  const onSelect = jest.fn();

  it("renders 4 example image buttons", () => {
    render(<ExampleImages selectedId={null} onSelect={onSelect} />);
    expect(screen.getAllByRole("option")).toHaveLength(4);
  });

  it("marks selected example with aria-selected", () => {
    render(<ExampleImages selectedId={1} onSelect={onSelect} />);
    const options = screen.getAllByRole("option");
    expect(options[0]).toHaveAttribute("aria-selected", "true");
    expect(options[1]).toHaveAttribute("aria-selected", "false");
  });

  it("calls onSelect when an example is clicked", async () => {
    const user = userEvent.setup();
    render(<ExampleImages selectedId={null} onSelect={onSelect} />);
    await user.click(screen.getAllByRole("option")[2]);
    expect(onSelect).toHaveBeenCalledWith(
      expect.objectContaining({ id: 3 })
    );
  });
});

describe("HowToUse", () => {
  it("renders the heading", () => {
    render(<HowToUse />);
    expect(
      screen.getByRole("heading", { name: /how to use/i })
    ).toBeInTheDocument();
  });

  it("renders all three instruction bullet points", () => {
    render(<HowToUse />);
    expect(screen.getByText(/select a model/i)).toBeInTheDocument();
    expect(screen.getByText(/select an example/i)).toBeInTheDocument();
    expect(screen.getByText(/click.*infer.*button/i)).toBeInTheDocument();
  });

  it("renders the Watch Demo button", () => {
    render(<HowToUse />);
    expect(
      screen.getByRole("button", { name: /watch demo/i })
    ).toBeInTheDocument();
  });
});

describe("ShareBar", () => {
  it("renders Facebook, Twitter, and copy link controls", () => {
    render(<ShareBar />);
    expect(screen.getByLabelText(/share on facebook/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/share on twitter/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/copy link/i)).toBeInTheDocument();
  });

  it("updates copy button label after clicking", async () => {
    Object.assign(navigator, {
      clipboard: { writeText: jest.fn().mockResolvedValue(undefined) },
    });
    const user = userEvent.setup();
    render(<ShareBar />);
    await user.click(screen.getByLabelText(/copy link/i));
    await waitFor(() =>
      expect(screen.getByLabelText(/link copied/i)).toBeInTheDocument()
    );
  });
});
