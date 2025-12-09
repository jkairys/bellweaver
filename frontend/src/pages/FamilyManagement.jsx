import React, { useState, useEffect } from 'react';
import ChildList from '../components/family/ChildList';
import ChildForm from '../components/family/ChildForm';
import OrganisationList from '../components/family/OrganisationList';
import OrganisationForm from '../components/family/OrganisationForm';
import {
  getChildren,
  createChild,
  updateChild,
  deleteChild,
    getOrganisations,
    createOrganisation,
    updateOrganisation,
    deleteOrganisation,
    createChannel,
    updateChannel,
    deleteChannel
  } from '../services/familyApi';
  import './FamilyManagement.css';
  
  function FamilyManagement() {
    const [children, setChildren] = useState([]);
    const [organisations, setOrganisations] = useState([]);
    const [loading, setLoading] = useState(false);
    
    // Tab State
    const [activeTab, setActiveTab] = useState('children'); // 'children' | 'organisations'
  
    // Child Form State
    const [showChildForm, setShowChildForm] = useState(false);
    const [editingChild, setEditingChild] = useState(null);
  
    // Organisation Form/Filter State
    const [showOrgForm, setShowOrgForm] = useState(false);
    const [editingOrg, setEditingOrg] = useState(null);
    const [orgTypeFilter, setOrgTypeFilter] = useState('');
  
    const [toast, setToast] = useState(null);
  
    // Show toast notification
    const showToast = (message, type = 'success') => {
      setToast({ message, type });
      setTimeout(() => setToast(null), 5000);
    };
  
    // Load data
    useEffect(() => {
      loadChildren();
      loadOrganisations();
    }, []);
  
    const loadChildren = async () => {
      setLoading(true);
      try {
        const data = await getChildren();
        setChildren(data);
      } catch (err) {
        showToast('Failed to load children: ' + err.message, 'error');
      } finally {
        setLoading(false);
      }
    };
  
    const loadOrganisations = async (type = null) => {
      setLoading(true);
      try {
        const data = await getOrganisations(type);
        setOrganisations(data);
      } catch (err) {
        showToast('Failed to load organisations: ' + err.message, 'error');
      } finally {
        setLoading(false);
      }
    };
  
    // --- Child Handlers ---
  
    const handleAddChild = () => {
      setEditingChild(null);
      setShowChildForm(true);
    };
  
    const handleEditChild = (child) => {
      setEditingChild(child);
      setShowChildForm(true);
    };
  
    const handleDeleteChild = async (child) => {
      if (!window.confirm(`Are you sure you want to delete ${child.name}? This action cannot be undone.`)) return;
  
      setLoading(true);
      try {
        await deleteChild(child.id);
        await loadChildren();
        showToast(`${child.name} has been deleted successfully`, 'success');
      } catch (err) {
        showToast('Failed to delete child: ' + err.message, 'error');
      } finally {
        setLoading(false);
      }
    };
  
    const handleSubmitChild = async (childData) => {
      setLoading(true);
      try {
        if (editingChild) {
          await updateChild(editingChild.id, childData);
          showToast(`${childData.name} has been updated successfully`, 'success');
        } else {
          await createChild(childData);
          showToast(`${childData.name} has been added successfully`, 'success');
        }
        await loadChildren();
        setShowChildForm(false);
        setEditingChild(null);
      } catch (err) {
        showToast('Failed to save child: ' + err.message, 'error');
      } finally {
        setLoading(false);
      }
    };
  
    const handleCancelChildForm = () => {
      setShowChildForm(false);
      setEditingChild(null);
    };
  
    // --- Organisation Handlers ---
  
    const handleAddOrg = () => {
      setEditingOrg(null);
      setShowOrgForm(true);
    };
  
    const handleEditOrg = async (org) => {
      setLoading(true);
      try {
        const fullOrg = await getOrganisation(org.id);
        setEditingOrg(fullOrg);
        setShowOrgForm(true);
      } catch (err) {
        showToast('Failed to load organisation details', 'error');
      } finally {
        setLoading(false);
      }
    };
  
    const handleDeleteOrg = async (org) => {
      if (!window.confirm(`Are you sure you want to delete ${org.name}?`)) return;
  
      setLoading(true);
      try {
        await deleteOrganisation(org.id);
        await loadOrganisations(orgTypeFilter || null);
        showToast(`${org.name} has been deleted successfully`, 'success');
      } catch (err) {
          showToast('Failed to delete organisation: ' + err.message, 'error');
      } finally {
        setLoading(false);
      }
    };
  
    const handleSubmitOrg = async (orgData) => {
      setLoading(true);
      try {
        if (editingOrg) {
          await updateOrganisation(editingOrg.id, orgData);
          showToast(`${orgData.name} has been updated successfully`, 'success');
        } else {
          await createOrganisation(orgData);
          showToast(`${orgData.name} has been added successfully`, 'success');
        }
        await loadOrganisations(orgTypeFilter || null);
        setShowOrgForm(false);
        setEditingOrg(null);
      } catch (err) {
        showToast('Failed to save organisation: ' + err.message, 'error');
      } finally {
        setLoading(false);
      }
    };
  
    const handleCancelOrgForm = () => {
      setShowOrgForm(false);
      setEditingOrg(null);
    };
    
    const handleOrgFilter = (type) => {
        setOrgTypeFilter(type);
        loadOrganisations(type || null);
    };
  
    // --- Channel Handlers ---
  
    const handleAddChannel = async (orgId, channelData) => {
        setLoading(true);
        try {
            await createChannel(orgId, channelData);
            showToast('Channel added successfully', 'success');
            // Refresh org details
            const fullOrg = await getOrganisation(orgId);
            setEditingOrg(fullOrg);
        } catch (err) {
            showToast('Failed to add channel: ' + err.message, 'error');
        } finally {
            setLoading(false);
        }
    };
  
    const handleUpdateChannel = async (channelId, channelData) => {
        setLoading(true);
        try {
            await updateChannel(channelId, channelData);
            showToast('Channel updated successfully', 'success');
             // Refresh org details
            if (editingOrg) {
               const fullOrg = await getOrganisation(editingOrg.id);
               setEditingOrg(fullOrg);
            }
        } catch (err) {
            showToast('Failed to update channel: ' + err.message, 'error');
        } finally {
            setLoading(false);
        }
    };
  
    const handleDeleteChannel = async (channelId) => {
        if (!window.confirm('Delete this channel?')) return;
        setLoading(true);
        try {
            await deleteChannel(channelId);
            showToast('Channel deleted successfully', 'success');
             // Refresh org details
            if (editingOrg) {
               const fullOrg = await getOrganisation(editingOrg.id);
               setEditingOrg(fullOrg);
            }
        } catch (err) {
            showToast('Failed to delete channel: ' + err.message, 'error');
        } finally {
            setLoading(false);
        }
    };
  
    return (
      <div className="family-management">
        <header className="page-header">
          <h1>Family Management</h1>
          <p>Manage your children's profiles and school information</p>
        </header>
  
        {toast && (
          <div className={`toast toast-${toast.type}`}>
            {toast.message}
            <button onClick={() => setToast(null)} className="toast-close">×</button>
          </div>
        )}
  
        {/* Tabs */}
        <div className="tabs">
          <button 
            className={`tab-btn ${activeTab === 'children' ? 'active' : ''}`}
            onClick={() => setActiveTab('children')}
          >
            Children
          </button>
          <button 
            className={`tab-btn ${activeTab === 'organisations' ? 'active' : ''}`}
            onClick={() => setActiveTab('organisations')}
          >
            Organisations
          </button>
        </div>
  
        <div className="page-actions">
          {activeTab === 'children' && !showChildForm && (
            <button onClick={handleAddChild} className="btn btn-primary">+ Add Child</button>
          )}
          {activeTab === 'organisations' && !showOrgForm && (
            <button onClick={handleAddOrg} className="btn btn-primary">+ Add Organisation</button>
          )}
        </div>
  
        {/* Children Tab Content */}
        {activeTab === 'children' && (
          <>
            {showChildForm ? (
              <ChildForm
                child={editingChild}
                onSubmit={handleSubmitChild}
                onCancel={handleCancelChildForm}
                loading={loading}
              />
            ) : (
              <ChildList
                children={children}
                onEdit={handleEditChild}
                onDelete={handleDeleteChild}
                loading={loading}
              />
            )}
          </>
        )}
  
        {/* Organisations Tab Content */}
        {activeTab === 'organisations' && (
          <>
            {showOrgForm ? (
              <OrganisationForm
                existingOrg={editingOrg}
                onSubmit={handleSubmitOrg}
                onCancel={handleCancelOrgForm}
                loading={loading}
                onAddChannel={handleAddChannel}
                onUpdateChannel={handleUpdateChannel}
                onDeleteChannel={handleDeleteChannel}
              />
            ) : (
              <OrganisationList
                organisations={organisations}
                onEdit={handleEditOrg}
                onDelete={handleDeleteOrg}
                onFilter={handleOrgFilter}
                loading={loading}
              />
            )}
          </>
        )}
      </div>
    );
  }
  
  export default FamilyManagement;
  