import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Users,
  Plus,
  Mail,
  Trash2,
  Crown,
  Shield,
  User,
  Loader2,
  X,
} from 'lucide-react'
import { organizationApi } from '@/lib/api'
import { useAuthStore } from '@/hooks/useAuth'
import type {
  Organization,
  OrganizationRole,
} from '@/types'
import { Alert } from '@/components/Alert'

const roleIcons: Record<OrganizationRole, React.ReactNode> = {
  owner: <Crown className="h-4 w-4 text-yellow-500" />,
  admin: <Shield className="h-4 w-4 text-blue-500" />,
  member: <User className="h-4 w-4 text-gray-500" />,
}

const roleLabels: Record<OrganizationRole, string> = {
  owner: 'Inhaber',
  admin: 'Administrator',
  member: 'Mitglied',
}

export function TeamPage() {
  const { user } = useAuthStore()
  const queryClient = useQueryClient()
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch organizations
  const { data: orgsData, isLoading: orgsLoading } = useQuery({
    queryKey: ['organizations'],
    queryFn: organizationApi.list,
  })

  // Fetch members when org is selected
  const { data: membersData, isLoading: membersLoading } = useQuery({
    queryKey: ['organization-members', selectedOrg?.id],
    queryFn: () => organizationApi.listMembers(selectedOrg!.id),
    enabled: !!selectedOrg,
  })

  // Create organization mutation
  const createOrgMutation = useMutation({
    mutationFn: organizationApi.create,
    onSuccess: (org) => {
      queryClient.invalidateQueries({ queryKey: ['organizations'] })
      setSelectedOrg(org)
      setShowCreateModal(false)
    },
    onError: (err: Error) => {
      setError(err.message || 'Fehler beim Erstellen der Organisation')
    },
  })

  // Invite member mutation
  const inviteMutation = useMutation({
    mutationFn: ({ orgId, email, role }: { orgId: string; email: string; role: 'admin' | 'member' }) =>
      organizationApi.inviteMember(orgId, { email, role }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['organization-members', selectedOrg?.id] })
      setShowInviteModal(false)
    },
    onError: (err: Error) => {
      setError(err.message || 'Fehler beim Einladen des Mitglieds')
    },
  })

  // Remove member mutation
  const removeMemberMutation = useMutation({
    mutationFn: ({ orgId, userId }: { orgId: string; userId: string }) =>
      organizationApi.removeMember(orgId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['organization-members', selectedOrg?.id] })
    },
  })

  // Update member role mutation
  const updateRoleMutation = useMutation({
    mutationFn: ({ orgId, userId, role }: { orgId: string; userId: string; role: 'admin' | 'member' }) =>
      organizationApi.updateMember(orgId, userId, { role }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['organization-members', selectedOrg?.id] })
    },
  })

  const currentUserMember = membersData?.members.find((m) => m.user_id === user?.id)
  const canManageMembers = currentUserMember?.role === 'owner' || currentUserMember?.role === 'admin'

  if (orgsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    )
  }

  const organizations = orgsData?.organizations || []

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Team</h1>
          <p className="text-gray-600 mt-1">
            Verwalten Sie Ihre Teams und Organisationen
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Team erstellen
        </button>
      </div>

      {error && (
        <Alert
          variant="error"
          title="Fehler"
          className="mb-6"
          onDismiss={() => setError(null)}
        >
          {error}
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Organizations list */}
        <div className="lg:col-span-1">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 p-4 border-b">
              Ihre Teams
            </h2>
            {organizations.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <Users className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>Sie sind noch in keinem Team.</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="text-primary-600 hover:text-primary-700 font-medium mt-2"
                >
                  Jetzt Team erstellen
                </button>
              </div>
            ) : (
              <div className="divide-y">
                {organizations.map((org) => (
                  <button
                    key={org.id}
                    onClick={() => setSelectedOrg(org)}
                    className={`w-full p-4 text-left hover:bg-gray-50 transition-colors ${
                      selectedOrg?.id === org.id ? 'bg-primary-50 border-l-2 border-primary-600' : ''
                    }`}
                  >
                    <div className="font-medium text-gray-900">{org.name}</div>
                    <div className="text-sm text-gray-500 mt-1">
                      {org.member_count} {org.member_count === 1 ? 'Mitglied' : 'Mitglieder'}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Selected organization details */}
        <div className="lg:col-span-2">
          {selectedOrg ? (
            <div className="card">
              <div className="p-4 border-b flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    {selectedOrg.name}
                  </h2>
                  {selectedOrg.description && (
                    <p className="text-sm text-gray-600 mt-1">{selectedOrg.description}</p>
                  )}
                </div>
                {canManageMembers && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setShowInviteModal(true)}
                      className="btn-primary flex items-center gap-2"
                    >
                      <Mail className="h-4 w-4" />
                      Einladen
                    </button>
                  </div>
                )}
              </div>

              {/* Usage stats */}
              <div className="p-4 border-b bg-gray-50">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-gray-900">
                      {selectedOrg.member_count || 0}
                    </div>
                    <div className="text-sm text-gray-500">Mitglieder</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-gray-900">
                      {selectedOrg.validations_this_month}
                    </div>
                    <div className="text-sm text-gray-500">Validierungen</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-gray-900">
                      {selectedOrg.conversions_this_month}
                    </div>
                    <div className="text-sm text-gray-500">Konvertierungen</div>
                  </div>
                </div>
              </div>

              {/* Members list */}
              <div className="p-4">
                <h3 className="font-medium text-gray-900 mb-4">Mitglieder</h3>
                {membersLoading ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-primary-600" />
                  </div>
                ) : (
                  <div className="space-y-3">
                    {membersData?.members.map((member) => (
                      <div
                        key={member.id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                            <span className="text-primary-700 font-medium">
                              {member.email[0].toUpperCase()}
                            </span>
                          </div>
                          <div>
                            <div className="font-medium text-gray-900">
                              {member.full_name || member.email}
                            </div>
                            {member.full_name && (
                              <div className="text-sm text-gray-500">{member.email}</div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="flex items-center gap-1 text-sm text-gray-600">
                            {roleIcons[member.role]}
                            {roleLabels[member.role]}
                          </span>
                          {canManageMembers && member.role !== 'owner' && member.user_id !== user?.id && (
                            <div className="flex items-center gap-1">
                              <select
                                value={member.role}
                                onChange={(e) =>
                                  updateRoleMutation.mutate({
                                    orgId: selectedOrg.id,
                                    userId: member.user_id,
                                    role: e.target.value as 'admin' | 'member',
                                  })
                                }
                                className="text-sm border rounded px-2 py-1"
                              >
                                <option value="member">Mitglied</option>
                                <option value="admin">Admin</option>
                              </select>
                              <button
                                onClick={() =>
                                  removeMemberMutation.mutate({
                                    orgId: selectedOrg.id,
                                    userId: member.user_id,
                                  })
                                }
                                className="p-1 text-gray-400 hover:text-error-600"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="card p-8 text-center text-gray-500">
              <Users className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <p className="text-lg font-medium text-gray-900 mb-2">
                Waehlen Sie ein Team aus
              </p>
              <p>
                Klicken Sie auf ein Team in der Liste, um die Mitglieder zu verwalten.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Create organization modal */}
      {showCreateModal && (
        <CreateOrganizationModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={(name, description) =>
            createOrgMutation.mutate({ name, description })
          }
          isLoading={createOrgMutation.isPending}
        />
      )}

      {/* Invite member modal */}
      {showInviteModal && selectedOrg && (
        <InviteMemberModal
          orgName={selectedOrg.name}
          onClose={() => setShowInviteModal(false)}
          onSubmit={(email, role) =>
            inviteMutation.mutate({ orgId: selectedOrg.id, email, role })
          }
          isLoading={inviteMutation.isPending}
        />
      )}
    </div>
  )
}

function CreateOrganizationModal({
  onClose,
  onSubmit,
  isLoading,
}: {
  onClose: () => void
  onSubmit: (name: string, description?: string) => void
  isLoading: boolean
}) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Team erstellen</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            onSubmit(name, description || undefined)
          }}
          className="p-4 space-y-4"
        >
          <div>
            <label className="label">Teamname *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input"
              placeholder="z.B. Meine Steuerkanzlei"
              required
              minLength={2}
            />
          </div>
          <div>
            <label className="label">Beschreibung (optional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input"
              rows={3}
              placeholder="Kurze Beschreibung des Teams..."
            />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="btn-secondary">
              Abbrechen
            </button>
            <button type="submit" disabled={isLoading} className="btn-primary">
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Erstellen...
                </>
              ) : (
                'Team erstellen'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function InviteMemberModal({
  orgName,
  onClose,
  onSubmit,
  isLoading,
}: {
  orgName: string
  onClose: () => void
  onSubmit: (email: string, role: 'admin' | 'member') => void
  isLoading: boolean
}) {
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<'admin' | 'member'>('member')

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Mitglied einladen</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            onSubmit(email, role)
          }}
          className="p-4 space-y-4"
        >
          <p className="text-sm text-gray-600">
            Laden Sie jemanden ein, dem Team <strong>{orgName}</strong> beizutreten.
          </p>
          <div>
            <label className="label">E-Mail-Adresse *</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              placeholder="kollege@beispiel.de"
              required
            />
          </div>
          <div>
            <label className="label">Rolle</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as 'admin' | 'member')}
              className="input"
            >
              <option value="member">Mitglied - Kann validieren und konvertieren</option>
              <option value="admin">Admin - Kann auch Mitglieder verwalten</option>
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="btn-secondary">
              Abbrechen
            </button>
            <button type="submit" disabled={isLoading} className="btn-primary">
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Einladen...
                </>
              ) : (
                'Einladung senden'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default TeamPage
