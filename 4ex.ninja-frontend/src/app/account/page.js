'use client';

import { AccountErrorBoundary } from '@/components/error';
import { useAuth, useProfileManagement } from '@/hooks/api';
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
  const [subscriptionData, setSubscriptionData] = useState({
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

    // Fetch subscription status from MongoDB API when authenticated
    if (isAuthenticated) {
      fetchSubscriptionStatus();
    }
  }, [authLoading, isAuthenticated, router, profile]);

  // Fetch subscription status from MongoDB API
  const fetchSubscriptionStatus = async () => {
    try {
      setSubscriptionLoading(true);
      const response = await fetch('/api/subscription-status');
      if (response.ok) {
        const data = await response.json();
        setSubscriptionData({
          isSubscribed: data.isSubscribed,
          subscriptionEnds: data.subscriptionEnds,
          status: data.status,
        });
      } else {
        console.error('Failed to fetch subscription status');
      }
    } catch (error) {
      console.error('Error fetching subscription status:', error);
    } finally {
      setSubscriptionLoading(false);
    }
  };

  // Handle update success/error messages
  useEffect(() => {
    if (updateSuccess) {
      setMessage({
        type: 'success',
        text: 'Profile updated successfully!',
      });
      // Clear form fields for password update
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
      resetUpdateState();
    }

    if (updateError) {
      setMessage({
        type: 'error',
        text: updateError,
      });
    }
  }, [updateSuccess, updateError, resetUpdateState]);

  // Format date for display
  const formatDate = dateString => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    }).format(date);
  };

  // Calculate days remaining in subscription
  const getDaysRemaining = endDate => {
    if (!endDate) return 0;

    const end = new Date(endDate);
    const now = new Date();
    const diffTime = end - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    return diffDays > 0 ? diffDays : 0;
  };

  const handleRenewSubscription = async () => {
    try {
      await handleCheckout();
    } catch (error) {
      console.error('Error renewing subscription:', error);
      setMessage({
        type: 'error',
        text: 'Failed to process subscription renewal.',
      });
    }
  };

  const handleCancelSubscription = async () => {
    // Add confirmation dialog
    if (
      !confirm(
        "Are you sure you want to cancel your subscription? You'll still have access until the billing period ends."
      )
    ) {
      return;
    }

    setMessage({ type: '', text: '' });
    setIsCanceling(true);

    try {
      const response = await fetch('/api/subscription/cancel', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (response.ok) {
        setMessage({
          type: 'success',
          text: data.message || 'Subscription canceled successfully.',
        });
        // Refresh subscription status
        await fetchSubscriptionStatus();
      } else {
        setMessage({
          type: 'error',
          text: data.message || 'Failed to cancel subscription. Please try again.',
        });
      }
    } catch (error) {
      console.error('Error cancelling subscription:', error);
      setMessage({
        type: 'error',
        text: 'Failed to cancel subscription. Please try again.',
      });
    } finally {
      setIsCanceling(false);
    }
  };

  const handleUpdateProfile = async e => {
    e.preventDefault();
    setMessage({ type: '', text: '' });

    try {
      // Validate passwords if attempting to change
      if (newPassword) {
        if (newPassword !== confirmNewPassword) {
          setMessage({ type: 'error', text: 'New passwords do not match.' });
          return;
        }

        if (newPassword.length < 6) {
          setMessage({
            type: 'error',
            text: 'New password must be at least 6 characters.',
          });
          return;
        }

        // Update password separately
        updatePassword({
          currentPassword,
          newPassword,
          confirmNewPassword,
        });
      } else {
        // Update profile information
        updateProfile({
          name,
          email,
        });
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      setMessage({
        type: 'error',
        text: error.message || 'Failed to update profile. Please try again.',
      });
    }
  };

  // Loading state
  if (authLoading || profileLoading) {
    return (
      <div className="min-h-screen bg-black flex justify-center items-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
      </div>
    );
  }

  // Subscription Tab content rendering
  const renderSubscriptionTab = () => {
    return (
      <div>
        <h2 className="text-2xl font-bold mb-6">Subscription Details</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Subscription Status */}
          <div className="bg-gray-900 rounded-lg p-6">
            <h3 className="text-xl font-medium mb-4">Status</h3>

            {subscriptionLoading ? (
              <div className="flex justify-center my-8">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-green-500"></div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-400">Plan</span>
                  <span className="font-medium">4ex.ninja Access</span>
                </div>

                <div className="flex justify-between">
                  <span className="text-gray-400">Status</span>
                  <span
                    className={`font-medium ${
                      subscriptionData.isSubscribed ? 'text-green-500' : 'text-red-500'
                    }`}
                  >
                    {subscriptionData.isSubscribed ? 'Active' : 'Inactive'}
                  </span>
                </div>

                <div className="flex justify-between">
                  <span className="text-gray-400">Price</span>
                  <span className="font-medium">$9.99/month</span>
                </div>

                <div className="flex justify-between">
                  <span className="text-gray-400">Next billing date</span>
                  <span className="font-medium">
                    {formatDate(subscriptionData.subscriptionEnds)}
                  </span>
                </div>

                {subscriptionData.subscriptionEnds && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Days remaining</span>
                    <span className="font-medium">
                      {getDaysRemaining(subscriptionData.subscriptionEnds)}
                    </span>
                  </div>
                )}
              </div>
            )}

            <div className="mt-6 pt-6 border-t border-gray-700">
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={handleRenewSubscription}
                  disabled={isUpdating || subscriptionLoading}
                  className="bg-green-700 hover:bg-green-800 text-white py-2 px-4 rounded-md flex-1 transition-colors disabled:opacity-50"
                >
                  {isUpdating ? 'Processing...' : 'Renew Subscription'}
                </button>

                <button
                  onClick={handleCancelSubscription}
                  disabled={isCanceling || subscriptionLoading || !subscriptionData.isSubscribed}
                  className="border border-red-500 text-red-500 hover:bg-red-500/10 py-2 px-4 rounded-md flex-1 transition-colors disabled:opacity-50"
                >
                  {isCanceling ? 'Processing...' : 'Cancel Subscription'}
                </button>
              </div>
            </div>
          </div>

          {/* Subscription Benefits */}
          <div className="bg-gray-900 rounded-lg p-6">
            <h3 className="text-xl font-medium mb-4">Your Benefits</h3>

            <ul className="space-y-3">
              <li className="flex items-start">
                <svg
                  className="w-5 h-5 text-green-500 mr-3 mt-1"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  ></path>
                </svg>
                <span>Real-time trading signals</span>
              </li>
              <li className="flex items-start">
                <svg
                  className="w-5 h-5 text-green-500 mr-3 mt-1"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  ></path>
                </svg>
                <span>Market analysis & insights</span>
              </li>
              <li className="flex items-start">
                <svg
                  className="w-5 h-5 text-green-500 mr-3 mt-1"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  ></path>
                </svg>
                <span>Strategy backtesting</span>
              </li>
              <li className="flex items-start">
                <svg
                  className="w-5 h-5 text-green-500 mr-3 mt-1"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  ></path>
                </svg>
                <span>Risk management tools</span>
              </li>
              <li className="flex items-start">
                <svg
                  className="w-5 h-5 text-green-500 mr-3 mt-1"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  ></path>
                </svg>
                <span>24/7 support</span>
              </li>
              <li className="flex items-start">
                <svg
                  className="w-5 h-5 text-green-500 mr-3 mt-1"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  ></path>
                </svg>
                <span>Trading community access</span>
              </li>
            </ul>

            <div className="mt-6 pt-6 border-t border-gray-700">
              <p className="text-gray-400 text-sm">
                Need help with your subscription? Contact our support team at{' '}
                <a href="mailto:support@4ex.ninja" className="text-green-500">
                  support@4ex.ninja
                </a>
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Main content
  return (
    <div className="min-h-screen bg-black text-white py-12 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-10 text-center">
          <h1 className="text-4xl font-bold mb-2">Account Settings</h1>
          <p className="text-gray-400">Manage your 4ex.ninja account and subscription</p>
        </div>

        {/* Tabs */}
        <div className="flex flex-wrap border-b border-gray-700 mb-8">
          <button
            onClick={() => setActiveTab('subscription')}
            className={`py-3 px-6 font-medium text-sm focus:outline-none transition-colors ${
              activeTab === 'subscription'
                ? 'border-b-2 border-green-500 text-green-500'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            Subscription
          </button>
          <button
            onClick={() => setActiveTab('profile')}
            className={`py-3 px-6 font-medium text-sm focus:outline-none transition-colors ${
              activeTab === 'profile'
                ? 'border-b-2 border-green-500 text-green-500'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            Profile
          </button>
          <button
            onClick={() => setActiveTab('security')}
            className={`py-3 px-6 font-medium text-sm focus:outline-none transition-colors ${
              activeTab === 'security'
                ? 'border-b-2 border-green-500 text-green-500'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            Security
          </button>
        </div>

        {/* Alert messages */}
        {message.text && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className={`mb-6 p-4 rounded ${
              message.type === 'error'
                ? 'bg-red-500/20 text-red-400'
                : 'bg-green-500/20 text-green-500'
            }`}
          >
            {message.text}
          </motion.div>
        )}

        {/* Tab content */}
        <div className="bg-gray-800 rounded-xl p-6 md:p-8">
          {/* Subscription Tab */}
          {activeTab === 'subscription' && renderSubscriptionTab()}

          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <div>
              <h2 className="text-2xl font-bold mb-6">Profile Information</h2>

              <form onSubmit={handleUpdateProfile}>
                <div className="space-y-6">
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-gray-400 mb-2">
                      Full Name
                    </label>
                    <input
                      id="name"
                      type="text"
                      value={name}
                      onChange={e => setName(e.target.value)}
                      className="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-4 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                      required
                    />
                  </div>

                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-400 mb-2">
                      Email Address
                    </label>
                    <input
                      id="email"
                      type="email"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      className="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-4 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                      required
                    />
                  </div>

                  <div className="pt-4 border-t border-gray-700">
                    <button
                      type="submit"
                      disabled={isUpdating}
                      className="bg-green-700 hover:bg-green-800 text-white py-2 px-6 rounded-md transition-colors"
                    >
                      {isUpdating ? 'Saving...' : 'Save Changes'}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <div>
              <h2 className="text-2xl font-bold mb-6">Security Settings</h2>

              <form onSubmit={handleUpdateProfile}>
                <div className="space-y-6">
                  <div>
                    <label
                      htmlFor="current-password"
                      className="block text-sm font-medium text-gray-400 mb-2"
                    >
                      Current Password
                    </label>
                    <input
                      id="current-password"
                      type="password"
                      value={currentPassword}
                      onChange={e => setCurrentPassword(e.target.value)}
                      className="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-4 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="new-password"
                      className="block text-sm font-medium text-gray-400 mb-2"
                    >
                      New Password
                    </label>
                    <input
                      id="new-password"
                      type="password"
                      value={newPassword}
                      onChange={e => setNewPassword(e.target.value)}
                      className="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-4 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="confirm-password"
                      className="block text-sm font-medium text-gray-400 mb-2"
                    >
                      Confirm New Password
                    </label>
                    <input
                      id="confirm-password"
                      type="password"
                      value={confirmNewPassword}
                      onChange={e => setConfirmNewPassword(e.target.value)}
                      className="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-4 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>

                  <div className="pt-4 border-t border-gray-700">
                    <button
                      type="submit"
                      disabled={isUpdating || (!currentPassword && !newPassword)}
                      className="bg-green-700 hover:bg-green-800 text-white py-2 px-6 rounded-md transition-colors disabled:opacity-50"
                    >
                      {isUpdating ? 'Updating...' : 'Update Password'}
                    </button>
                  </div>
                </div>
              </form>

              <div className="mt-12 pt-6 border-t border-gray-700">
                <h3 className="text-xl font-medium mb-4">Account Actions</h3>

                <button
                  onClick={() => {
                    if (confirm('Are you sure you want to sign out from all devices?')) {
                      // Implement force sign out from all devices
                    }
                  }}
                  className="bg-gray-700 hover:bg-gray-600 text-white py-2 px-6 rounded-md transition-colors mb-3"
                >
                  Sign Out From All Devices
                </button>

                <button
                  onClick={() => {
                    if (
                      confirm(
                        'Are you sure you want to delete your account? This action cannot be undone.'
                      )
                    ) {
                      // Implement account deletion logic
                    }
                  }}
                  className="block bg-red-900/30 border border-red-800 text-red-400 py-2 px-6 rounded-md hover:bg-red-800/30 transition-colors"
                >
                  Delete Account
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Wrap the component with AccountErrorBoundary
export default function AccountPage() {
  return (
    <AccountErrorBoundary>
      <AccountPageComponent />
    </AccountErrorBoundary>
  );
}
