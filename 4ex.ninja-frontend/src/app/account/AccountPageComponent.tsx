'use client';

import { AccountErrorBoundary } from '@/components/error';
import { useAuth, useProfileManagement } from '@/hooks/api';
import { AccountSkeleton } from '@/components/ui';
import { handleCheckout } from '@/utils/checkout-helpers';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

function AccountPageComponent() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const {
    profile,
    isLoading: profileLoading,
    updateProfile,
    updatePassword,
    isUpdating,
    updateError,
    updateSuccess,
    resetUpdateState,
  } = useProfileManagement();

  // Subscription state managed directly with MongoDB API
  const [subscriptionData, setSubscriptionData] = useState<{
    isSubscribed: boolean;
    subscriptionEnds: string | null;
    status: string | null;
  }>({
    isSubscribed: false,
    subscriptionEnds: null,
    status: null,
  });
  const [subscriptionLoading, setSubscriptionLoading] = useState(true);
  const [isCanceling, setIsCanceling] = useState(false);

  const [activeTab, setActiveTab] = useState('subscription');
  const [message, setMessage] = useState({ type: '', text: '' });
  const router = useRouter();

  // Form states for profile update
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login?callbackUrl=/account');
    }

    if (profile) {
      setName(profile.name || '');
      setEmail(profile.email || '');
    }
  }, [authLoading, isAuthenticated, profile, router]);

  // Fetch subscription status on component mount using direct MongoDB API
  useEffect(() => {
    const fetchSubscriptionStatus = async () => {
      try {
        setSubscriptionLoading(true);
        const response = await fetch('/api/subscription-status', {
          credentials: 'include',
        });
        const data = await response.json();

        if (response.ok) {
          setSubscriptionData({
            isSubscribed: data.isSubscribed,
            subscriptionEnds: data.subscriptionEnds,
            status: data.status,
          });
        } else {
          console.error('Failed to fetch subscription status:', data.error);
        }
      } catch (error) {
        console.error('Error fetching subscription status:', error);
      } finally {
        setSubscriptionLoading(false);
      }
    };

    if (isAuthenticated) {
      fetchSubscriptionStatus();
    }
  }, [isAuthenticated]);

  const handleCancel = async () => {
    setIsCanceling(true);
    try {
      const response = await fetch('/api/cancel-subscription', {
        method: 'POST',
        credentials: 'include',
      });

      const data = await response.json();

      if (response.ok) {
        setMessage({ type: 'success', text: 'Subscription cancelled successfully' });
        // Refresh subscription data
        setSubscriptionData(prev => ({ ...prev, status: 'cancelled' }));
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to cancel subscription' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to cancel subscription' });
    } finally {
      setIsCanceling(false);
    }
  };

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    resetUpdateState();

    if (!name.trim() || !email.trim()) {
      setMessage({ type: 'error', text: 'Name and email are required' });
      return;
    }

    const updateData = { name: name.trim(), email: email.trim() };
    await updateProfile(updateData);
  };

  const handlePasswordUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    resetUpdateState();

    if (!currentPassword || !newPassword) {
      setMessage({ type: 'error', text: 'Current password and new password are required' });
      return;
    }

    if (newPassword !== confirmNewPassword) {
      setMessage({ type: 'error', text: 'New passwords do not match' });
      return;
    }

    if (newPassword.length < 6) {
      setMessage({ type: 'error', text: 'New password must be at least 6 characters' });
      return;
    }

    await updatePassword({ currentPassword, newPassword, confirmNewPassword });

    // Clear password fields on successful update
    if (!updateError) {
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
    }
  };

  // Show loading spinner while checking authentication
  if (authLoading || profileLoading || subscriptionLoading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-2xl bg-black min-h-screen">
        <h1 className="text-3xl font-bold mb-6">Account Settings</h1>
        <AccountSkeleton />
      </div>
    );
  }

  // Redirect happens in useEffect, show loading during redirect
  if (!isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-2xl bg-black min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
          <p className="mt-2">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl bg-black text-white min-h-screen">
      <h1 className="text-3xl font-bold mb-6">Account Settings</h1>

      {/* Tab Navigation */}
      <div className="flex space-x-4 mb-6 border-b border-gray-700">
        <button
          onClick={() => setActiveTab('subscription')}
          className={`pb-2 px-1 ${
            activeTab === 'subscription'
              ? 'border-b-2 border-green-500 text-green-500'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          Subscription
        </button>
        <button
          onClick={() => setActiveTab('profile')}
          className={`pb-2 px-1 ${
            activeTab === 'profile'
              ? 'border-b-2 border-green-500 text-green-500'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          Profile
        </button>
        <button
          onClick={() => setActiveTab('password')}
          className={`pb-2 px-1 ${
            activeTab === 'password'
              ? 'border-b-2 border-green-500 text-green-500'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          Password
        </button>
      </div>

      {/* Messages */}
      {message.text && (
        <div
          className={`mb-4 p-4 rounded-md ${
            message.type === 'success'
              ? 'bg-green-900/20 text-green-400 border border-green-800'
              : 'bg-red-900/20 text-red-400 border border-red-800'
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Update messages from useProfileManagement */}
      {updateError && (
        <div className="mb-4 p-4 rounded-md bg-red-900/20 text-red-400 border border-red-800">
          {updateError}
        </div>
      )}

      {updateSuccess && (
        <div className="mb-4 p-4 rounded-md bg-green-900/20 text-green-400 border border-green-800">
          {updateSuccess}
        </div>
      )}

      {/* Subscription Tab */}
      {activeTab === 'subscription' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="space-y-6"
        >
          {subscriptionLoading ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
              <p className="mt-2">Loading subscription details...</p>
            </div>
          ) : (
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Subscription Status</h2>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Status:</span>
                  <span
                    className={
                      subscriptionData.isSubscribed
                        ? 'text-green-400 font-semibold'
                        : 'text-red-400 font-semibold'
                    }
                  >
                    {subscriptionData.isSubscribed ? 'Active' : 'Inactive'}
                  </span>
                </div>
                {subscriptionData.subscriptionEnds && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Ends:</span>
                    <span className="text-white">
                      {new Date(subscriptionData.subscriptionEnds).toLocaleDateString()}
                    </span>
                  </div>
                )}
                {subscriptionData.status && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Stripe Status:</span>
                    <span className="text-white capitalize">{subscriptionData.status}</span>
                  </div>
                )}
              </div>

              <div className="mt-6 space-y-3">
                {subscriptionData.isSubscribed ? (
                  <button
                    onClick={handleCancel}
                    disabled={isCanceling}
                    className="w-full bg-red-600 hover:bg-red-700 disabled:bg-red-800 text-white py-2 px-4 rounded-md transition-colors duration-200"
                  >
                    {isCanceling ? 'Canceling...' : 'Cancel Subscription'}
                  </button>
                ) : (
                  <button
                    onClick={() => handleCheckout()}
                    className="w-full bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-md transition-colors duration-200"
                  >
                    Subscribe Now
                  </button>
                )}
                <p className="text-sm text-gray-400 text-center">
                  {subscriptionData.isSubscribed
                    ? 'Canceling will stop automatic renewal'
                    : 'Get access to premium trading signals'}
                </p>
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Profile Information</h2>
            {profileLoading ? (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                <p className="mt-2">Loading profile...</p>
              </div>
            ) : (
              <form onSubmit={handleProfileUpdate} className="space-y-4">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-1">
                    Name
                  </label>
                  <input
                    type="text"
                    id="name"
                    value={name}
                    onChange={e => setName(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    id="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={isUpdating}
                  className="w-full bg-green-600 hover:bg-green-700 disabled:bg-green-800 text-white py-2 px-4 rounded-md transition-colors duration-200"
                >
                  {isUpdating ? 'Updating...' : 'Update Profile'}
                </button>
              </form>
            )}
          </div>
        </motion.div>
      )}

      {/* Password Tab */}
      {activeTab === 'password' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Change Password</h2>
            <form onSubmit={handlePasswordUpdate} className="space-y-4">
              <div>
                <label
                  htmlFor="currentPassword"
                  className="block text-sm font-medium text-gray-300 mb-1"
                >
                  Current Password
                </label>
                <input
                  type="password"
                  id="currentPassword"
                  value={currentPassword}
                  onChange={e => setCurrentPassword(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label
                  htmlFor="newPassword"
                  className="block text-sm font-medium text-gray-300 mb-1"
                >
                  New Password
                </label>
                <input
                  type="password"
                  id="newPassword"
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  required
                  minLength={6}
                />
              </div>
              <div>
                <label
                  htmlFor="confirmNewPassword"
                  className="block text-sm font-medium text-gray-300 mb-1"
                >
                  Confirm New Password
                </label>
                <input
                  type="password"
                  id="confirmNewPassword"
                  value={confirmNewPassword}
                  onChange={e => setConfirmNewPassword(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  required
                  minLength={6}
                />
              </div>
              <button
                type="submit"
                disabled={isUpdating}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-green-800 text-white py-2 px-4 rounded-md transition-colors duration-200"
              >
                {isUpdating ? 'Updating...' : 'Update Password'}
              </button>
            </form>
          </div>
        </motion.div>
      )}
    </div>
  );
}

export default function AccountPageWithBoundary() {
  return (
    <AccountErrorBoundary>
      <AccountPageComponent />
    </AccountErrorBoundary>
  );
}
