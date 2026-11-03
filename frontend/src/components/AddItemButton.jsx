import { Plus } from "lucide-react";
import "../styles/offer-editing.css";

export function AddItemButton({ children, help, icon: Icon = Plus, ...props }) {
  return <button type="button" className="offer-add-action" {...props}><span className="offer-add-icon"><Icon size={19} /></span><span><strong>{children}</strong>{help && <small>{help}</small>}</span>{Icon !== Plus && <Plus size={17} className="offer-add-plus" />}</button>;
}
