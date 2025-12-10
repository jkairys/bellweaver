import React, { useState, useEffect } from 'react';
import type { Organisation } from '../../types/api';
import ChannelConfig from './ChannelConfig';
import './OrganisationForm.css';

interface OrganisationFormProps {
  existingOrg: any | null;
  onSubmit: (data: any) => void;
  onCancel: () => void;
  loading: boolean;
  onAddChannel?: (orgId: string, data: any) => void;
  onUpdateChannel?: (channelId: string, data: any) => void;
  onDeleteChannel?: (channelId: string) => void;
}

interface ContactInfo {
  phone: string;
  email: string;
  website: string;
}

interface FormData {
  name: string;
  type: string;
  address: string;
  contact_info: ContactInfo;
}

function OrganisationForm({ existingOrg, onSubmit, onCancel, loading, onAddChannel, onUpdateChannel, onDeleteChannel }: OrganisationFormProps) {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    type: 'school',
    address: '',
    contact_info: { phone: '', email: '', website: '' }
  });

  const [editingChannel, setEditingChannel] = useState<any>(null);
  const [showChannelForm, setShowChannelForm] = useState<boolean>(false);

  useEffect(() => {
    if (existingOrg) {
      setFormData({
        name: existingOrg.name,
        type: existingOrg.type,
        address: existingOrg.address || '',
        contact_info: {
          phone: existingOrg.contact_info?.phone || '',
          email: existingOrg.contact_info?.email || '',
          website: existingOrg.contact_info?.website || ''
        }
      });
    } else {
        setFormData({
            name: '',
            type: 'school',
            address: '',
            contact_info: { phone: '', email: '', website: '' }
        });
    }
  }, [existingOrg]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    if (name.startsWith('contact_')) {
      const field = name.replace('contact_', '') as keyof ContactInfo;
      setFormData(prev => ({
        ...prev,
        contact_info: { ...prev.contact_info, [field]: value }
      }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="organisation-form-container">
    <form onSubmit={handleSubmit} className="organisation-form">
      <h3>{existingOrg ? 'Edit Organisation' : 'Add Organisation'}</h3>

      <div className="form-group">
        <label>Name*</label>
        <input
          type="text"
          name="name"
          value={formData.name}
          onChange={handleChange}
          required
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label>Type*</label>
        <select name="type" value={formData.type} onChange={handleChange} disabled={loading}>
          <option value="school">School</option>
          <option value="daycare">Daycare</option>
          <option value="kindergarten">Kindergarten</option>
          <option value="sports_team">Sports Team</option>
          <option value="other">Other</option>
        </select>
      </div>

      <div className="form-group">
        <label>Address</label>
        <input
          type="text"
          name="address"
          value={formData.address}
          onChange={handleChange}
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label>Phone</label>
        <input
          type="tel"
          name="contact_phone"
          value={formData.contact_info.phone}
          onChange={handleChange}
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label>Email</label>
        <input
          type="email"
          name="contact_email"
          value={formData.contact_info.email}
          onChange={handleChange}
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label>Website</label>
        <input
          type="url"
          name="contact_website"
          value={formData.contact_info.website}
          onChange={handleChange}
          disabled={loading}
        />
      </div>

      <div className="form-actions">
        <button type="submit" disabled={loading} className="btn btn-primary">
          {loading ? 'Saving...' : 'Save'}
        </button>
        <button type="button" onClick={onCancel} disabled={loading} className="btn">Cancel</button>
      </div>
    </form>

    {existingOrg && (
        <div className="organisation-form-extras">
            {existingOrg.children && existingOrg.children.length > 0 && (
                <div className="associated-children">
                    <h4>Attending Children</h4>
                    <ul>
                        {existingOrg.children.map((child: any) => (
                            <li key={child.id}>{child.name}</li>
                        ))}
                    </ul>
                </div>
            )}

            <div className="channels-section">
                <h4>Communication Channels</h4>

                {!showChannelForm ? (
                    <>
                        <ul className="channel-list">
                            {existingOrg.channels && existingOrg.channels.map((ch: any) => (
                                <li key={ch.id} className="channel-item">
                                    <span>{ch.channel_type} ({ch.is_active ? 'Active' : 'Inactive'})</span>
                                    {ch.last_sync_status && (
                                        <span className={`status-badge ${ch.last_sync_status.toLowerCase()}`}>
                                            {ch.last_sync_status}
                                        </span>
                                    )}
                                    <button type="button" onClick={() => { setEditingChannel(ch); setShowChannelForm(true); }} className="btn btn-edit btn-sm">
                                        Edit
                                    </button>
                                </li>
                            ))}
                        </ul>
                        <button type="button" onClick={() => { setEditingChannel(null); setShowChannelForm(true); }} className="btn btn-primary btn-sm">
                            Add Channel
                        </button>
                    </>
                ) : (
                    <ChannelConfig
                        channel={editingChannel}
                        onSave={(data: any) => {
                            if (editingChannel && onUpdateChannel) {
                                onUpdateChannel(editingChannel.id, data);
                            } else if (onAddChannel) {
                                onAddChannel(existingOrg.id, data);
                            }
                            setShowChannelForm(false);
                        }}
                        onCancel={() => setShowChannelForm(false)}
                        onDelete={onDeleteChannel ? (id: string) => { onDeleteChannel(id); setShowChannelForm(false); } : null}
                        loading={loading}
                    />
                )}
            </div>
        </div>
    )}
    </div>
  );
}

export default OrganisationForm;
