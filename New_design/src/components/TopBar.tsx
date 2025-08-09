import React from 'react';
import { Bell, Search, User, LogOut } from 'lucide-react';
import { User as UserType } from '../types';

interface TopBarProps {
  user: UserType;
  sidebarCollapsed: boolean;
  onProfileClick: () => void;
  onLogout: () => void;
}

export function TopBar({ user, sidebarCollapsed, onProfileClick, onLogout }: TopBarProps) {
  return (
    <div className={`
      fixed top-0 right-0 h-16 bg-white/80 backdrop-blur-xl border-b border-gray-200 
      transition-all duration-300 z-30 flex items-center justify-between px-6
      ${sidebarCollapsed ? 'left-16' : 'left-64'}
    `}>
      {/* Search */}
      <div className="flex-1 max-w-lg">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search workflows, agents, knowledge sources..."
            className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
          />
        </div>
      </div>

      {/* Right Section */}
      <div className="flex items-center space-x-4">
        {/* Notifications */}
        <button className="p-2 rounded-lg hover:bg-gray-100 relative">
          <Bell className="w-5 h-5 text-gray-600" />
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
        </button>

        {/* User Profile */}
        <div className="flex items-center space-x-3">
          <div className="text-right">
            <p className="text-sm font-medium text-gray-900">{user.name}</p>
            <p className="text-xs text-gray-500 capitalize">{user.role}</p>
          </div>
          <div className="relative group">
            <img
              src={user.avatar}
              alt={user.name}
              className="w-10 h-10 rounded-full border-2 border-purple-200"
            />
            <div className="absolute right-0 top-12 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 py-2">
              <button 
                onClick={onProfileClick}
                className="w-full flex items-center space-x-2 px-4 py-2 hover:bg-gray-50 text-left"
              >
                <User className="w-4 h-4 text-gray-600" />
                <span className="text-sm text-gray-700">Profile</span>
              </button>
              <button 
                onClick={onLogout}
                className="w-full flex items-center space-x-2 px-4 py-2 hover:bg-gray-50 text-left"
              >
                <LogOut className="w-4 h-4 text-gray-600" />
                <span className="text-sm text-gray-700">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}