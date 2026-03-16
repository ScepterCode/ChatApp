/**
 * Unified API Client for Chat Application
 * Handles all API communication with consistent error handling and retry logic
 */

class ChatAPIClient {
    constructor(baseURL, token) {
        this.baseURL = baseURL;
        this.token = token;
        this.retryAttempts = 3;
        this.retryDelay = 1000;
    }

    /**
     * Make API request with error handling and retry logic
     */
    async request(method, endpoint, data = null, retryCount = 0) {
        try {
            const options = {
                method,
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                }
            };

            if (data) {
                options.body = JSON.stringify(data);
            }

            const response = await fetch(`${this.baseURL}${endpoint}`, options);

            // Handle 401 - Token expired
            if (response.status === 401) {
                localStorage.clear();
                window.location.href = '/login/';
                return null;
            }

            // Handle 500 - Server error, retry
            if (response.status === 500 && retryCount < this.retryAttempts) {
                await this.delay(this.retryDelay);
                return this.request(method, endpoint, data, retryCount + 1);
            }

            const responseData = await response.json();

            if (!response.ok) {
                throw new Error(responseData.message || `HTTP ${response.status}`);
            }

            return responseData;
        } catch (error) {
            console.error(`API Error [${method} ${endpoint}]:`, error);
            throw error;
        }
    }

    /**
     * Delay helper for retry logic
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Safe array extraction from response
     */
    safeArray(response) {
        if (Array.isArray(response)) return response;
        if (response && Array.isArray(response.results)) return response.results;
        if (response && Array.isArray(response.data)) return response.data;
        if (response && response.data && Array.isArray(response.data.items)) return response.data.items;
        return [];
    }

    // ==================== DIRECT MESSAGES ====================

    /**
     * Get all conversations
     */
    async getConversations() {
        const response = await this.request('GET', '/chat/direct-messages/conversations/');
        return this.safeArray(response);
    }

    /**
     * Get messages with specific user
     */
    async getMessages(userId) {
        const response = await this.request('GET', `/chat/direct-messages/with_user/?user_id=${userId}`);
        return this.safeArray(response);
    }

    /**
     * Send direct message
     */
    async sendMessage(recipientId, content) {
        return this.request('POST', '/chat/direct-messages/', {
            recipient: recipientId,
            content
        });
    }

    // ==================== GROUPS ====================

    /**
     * Get all groups with optional search
     */
    async getGroups(search = '') {
        const endpoint = search ? `/chat/rooms/?search=${encodeURIComponent(search)}` : '/chat/rooms/';
        const response = await this.request('GET', endpoint);
        return this.safeArray(response);
    }

    /**
     * Get group details
     */
    async getGroup(groupId) {
        return this.request('GET', `/chat/rooms/${groupId}/`);
    }

    /**
     * Create group
     */
    async createGroup(name) {
        return this.request('POST', '/chat/rooms/', { name });
    }

    /**
     * Delete group (admin only)
     */
    async deleteGroup(groupId) {
        return this.request('DELETE', `/chat/rooms/${groupId}/delete_room/`);
    }

    /**
     * Leave group
     */
    async leaveGroup(groupId) {
        return this.request('POST', `/chat/rooms/${groupId}/leave/`);
    }

    /**
     * Get group members with fallback
     */
    async getGroupMembers(groupId) {
        try {
            // Use memberships endpoint with room filter
            const response = await this.request('GET', `/chat/memberships/?room=${groupId}`);
            const memberships = this.safeArray(response);
            
            // Transform to match expected format for the template
            return memberships.map(membership => ({
                user: {
                    id: membership.user,
                    username: membership.user_username,
                    email: membership.user_email || ''
                },
                joined_at: membership.joined_at,
                is_admin: false // We'll need to get this from room data separately
            }));
        } catch (error) {
            console.error('Error loading group members:', error);
            return [];
        }
    }

    /**
     * Add member to group (admin only)
     */
    async addMemberToGroup(groupId, username) {
        return this.request('POST', `/chat/rooms/${groupId}/add_member/`, { username });
    }

    /**
     * Remove member from group (admin only)
     */
    async removeMemberFromGroup(groupId, userId) {
        return this.request('DELETE', `/chat/rooms/${groupId}/remove_member/`, { user_id: userId });
    }

    /**
     * Get group messages
     */
    async getGroupMessages(groupId) {
        const response = await this.request('GET', `/chat/messages/?room=${groupId}`);
        return this.safeArray(response);
    }

    /**
     * Send group message
     */
    async sendGroupMessage(groupId, content) {
        return this.request('POST', '/chat/messages/', {
            room: groupId,
            content
        });
    }

    // ==================== MEMBERS ====================

    /**
     * Add member to group
     */
    async addMember(groupId, username) {
        return this.request('POST', `/chat/rooms/${groupId}/add_member/`, { username });
    }

    /**
     * Remove member from group
     */
    async removeMember(groupId, userId) {
        return this.request('DELETE', `/chat/rooms/${groupId}/remove_member/`, { user_id: userId });
    }

    // ==================== USERS ====================

    /**
     * Search users
     */
    async searchUsers(query) {
        const response = await this.request('GET', `/auth/users/?search=${query}`);
        return this.safeArray(response);
    }

    /**
     * Get user profile
     */
    async getProfile() {
        return this.request('GET', '/auth/profile/');
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChatAPIClient;
}
