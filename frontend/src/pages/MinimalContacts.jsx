import { useState, useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import API from "../services/api";
import { 
  UserPlus, 
  Search, 
  Mail, 
  Phone, 
  Briefcase, 
  Tag, 
  Edit2, 
  Trash2, 
  Send,
  X,
  Plus,
  Users
} from "lucide-react";

export default function MinimalContacts() {
  const { token } = useAuth();
  const [contacts, setContacts] = useState([]);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    designation: "",
    tags: "",
  });

  useEffect(() => {
    if (token) fetchContacts();
  }, [token, search]);

  const fetchContacts = async () => {
    try {
      const res = await API.get(`/contacts${search ? `?q=${search}` : ""}`);
      setContacts(res.data);
    } catch (err) {
      console.error("Failed to fetch contacts:", err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await API.put(`/contacts/${editingId}`, formData);
      } else {
        await API.post("/contacts", formData);
      }
      resetForm();
      fetchContacts();
    } catch (err) {
      console.error("Failed to save contact:", err);
    }
  };

  const handleEdit = (contact) => {
    setEditingId(contact.id);
    setFormData({
      name: contact.name || "",
      email: contact.email || "",
      phone: contact.phone || "",
      designation: contact.designation || "",
      tags: contact.tags || "",
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!confirm("Delete this contact?")) return;
    try {
      await API.delete(`/contacts/${id}`);
      fetchContacts();
    } catch (err) {
      console.error("Failed to delete contact:", err);
    }
  };

  const resetForm = () => {
    setFormData({ name: "", email: "", phone: "", designation: "", tags: "" });
    setEditingId(null);
    setShowForm(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="minimal-container py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="minimal-heading minimal-heading-xl mb-2">Contacts</h1>
            <p className="minimal-text-secondary">Manage your business contacts</p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="minimal-button minimal-button-primary"
          >
            <UserPlus className="w-4 h-4 mr-2" />
            Add Contact
          </button>
        </div>

        {/* Search */}
        <div className="relative mb-6">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search contacts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="minimal-input pl-10"
          />
        </div>

        {/* Form Modal */}
        {showForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="minimal-card p-6 w-full max-w-md mx-4">
              <div className="flex items-center justify-between mb-6">
                <h2 className="minimal-heading minimal-heading-md">
                  {editingId ? "Edit Contact" : "New Contact"}
                </h2>
                <button
                  onClick={resetForm}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block minimal-text font-medium mb-2">Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    className="minimal-input"
                    placeholder="John Doe"
                  />
                </div>

                <div>
                  <label className="block minimal-text font-medium mb-2">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="minimal-input"
                    placeholder="john@company.com"
                  />
                </div>

                <div>
                  <label className="block minimal-text font-medium mb-2">Phone</label>
                  <input
                    type="text"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="minimal-input"
                    placeholder="+1 (555) 123-4567"
                  />
                </div>

                <div>
                  <label className="block minimal-text font-medium mb-2">Designation</label>
                  <input
                    type="text"
                    value={formData.designation}
                    onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                    className="minimal-input"
                    placeholder="CEO, Marketing Director"
                  />
                </div>

                <div>
                  <label className="block minimal-text font-medium mb-2">Tags</label>
                  <input
                    type="text"
                    value={formData.tags}
                    onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                    className="minimal-input"
                    placeholder="client, vendor, partner"
                  />
                </div>

                <div className="flex space-x-3 pt-4">
                  <button type="submit" className="minimal-button minimal-button-primary flex-1">
                    {editingId ? "Update" : "Create"}
                  </button>
                  <button
                    type="button"
                    onClick={resetForm}
                    className="minimal-button minimal-button-secondary"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Contacts Grid */}
        {contacts.length === 0 ? (
          <div className="minimal-card p-12 text-center">
            <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="minimal-heading minimal-heading-md mb-2">No contacts yet</h3>
            <p className="minimal-text-secondary mb-6">Add your first contact to get started</p>
            <button
              onClick={() => setShowForm(true)}
              className="minimal-button minimal-button-primary"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Contact
            </button>
          </div>
        ) : (
          <div className="minimal-grid minimal-grid-3">
            {contacts.map((contact) => (
              <div key={contact.id} className="minimal-card p-6 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="minimal-heading text-blue-600">
                      {contact.name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div className="flex space-x-1">
                    <button
                      onClick={() => handleEdit(contact)}
                      className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                      title="Edit"
                    >
                      <Edit2 className="w-4 h-4 text-gray-500" />
                    </button>
                    <button
                      onClick={() => handleDelete(contact.id)}
                      className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                    <button
                      onClick={() => alert(`Share to: ${contact.name}`)}
                      className="p-2 hover:bg-green-50 rounded-lg transition-colors"
                      title="Share"
                    >
                      <Send className="w-4 h-4 text-green-500" />
                    </button>
                  </div>
                </div>

                <h3 className="minimal-heading minimal-heading-sm mb-2">{contact.name}</h3>
                
                {contact.designation && (
                  <div className="flex items-center space-x-2 mb-2">
                    <Briefcase className="w-4 h-4 text-gray-400" />
                    <span className="minimal-text-secondary">{contact.designation}</span>
                  </div>
                )}

                {contact.email && (
                  <div className="flex items-center space-x-2 mb-2">
                    <Mail className="w-4 h-4 text-gray-400" />
                    <span className="minimal-text-secondary">{contact.email}</span>
                  </div>
                )}

                {contact.phone && (
                  <div className="flex items-center space-x-2 mb-3">
                    <Phone className="w-4 h-4 text-gray-400" />
                    <span className="minimal-text-secondary">{contact.phone}</span>
                  </div>
                )}

                {contact.tags && (
                  <div className="flex items-center space-x-2">
                    <Tag className="w-4 h-4 text-gray-400" />
                    <div className="flex flex-wrap gap-1">
                      {contact.tags.split(',').map((tag, index) => (
                        <span key={index} className="status-indicator status-info">
                          {tag.trim()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
