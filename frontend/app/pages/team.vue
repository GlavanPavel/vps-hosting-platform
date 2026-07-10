<template>
	<div>
		<div class="mb-7">
			<h1 class="text-2xl font-bold text-slate-900">
				Team
			</h1>
			<p class="text-sm text-slate-500 mt-1">
				People in your organization. Everyone shares the same instances, networks, and storage.
			</p>
		</div>

		<!-- add member (owners only) -->
		<div
			v-if="isOwner"
			class="bg-white rounded-xl shadow-sm border border-slate-200/70 p-6 mb-8"
		>
			<h2 class="font-semibold text-slate-900 mb-4">
				Add a member
			</h2>
			<form
				class="flex items-end gap-4 flex-wrap"
				@submit.prevent="addMember"
			>
				<div class="flex flex-col gap-2 flex-1 min-w-[200px]">
					<label class="text-sm font-medium text-slate-700">Email</label>
					<input
						v-model="form.email"
						type="email"
						required
						placeholder="teammate@example.com"
						class="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
					>
				</div>
				<div class="flex flex-col gap-2 flex-1 min-w-[180px]">
					<label class="text-sm font-medium text-slate-700">Temporary password</label>
					<input
						v-model="form.password"
						type="text"
						required
						minlength="8"
						placeholder="at least 8 characters"
						class="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
					>
				</div>
				<div class="flex flex-col gap-2 w-36">
					<label class="text-sm font-medium text-slate-700">Role</label>
					<select
						v-model="form.role"
						class="w-full rounded-lg border border-slate-300 px-3 py-2.5 bg-white outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
					>
						<option value="member">
							Member
						</option>
						<option value="owner">
							Owner
						</option>
					</select>
				</div>
				<button
					type="submit"
					:disabled="submitting"
					class="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-60 text-white font-medium py-2.5 px-5 rounded-lg transition-colors"
				>
					<Icon
						name="solar:user-plus-outline"
						class="text-lg"
					/>
					{{ submitting ? "Adding…" : "Add member" }}
				</button>
			</form>
			<p
				v-if="error"
				class="text-red-600 text-sm mt-3"
			>
				{{ error }}
			</p>
			<p class="text-xs text-slate-400 mt-3">
				The member signs in with this email + password. Owners can manage members; members can
				use all resources but can't manage the team.
			</p>
		</div>

		<div class="bg-white rounded-xl shadow-sm border border-slate-200/70 overflow-hidden">
			<table class="w-full text-left">
				<thead class="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
					<tr>
						<th class="py-3 px-5 font-semibold">
							Email
						</th>
						<th class="py-3 px-5 font-semibold">
							Role
						</th>
						<th class="py-3 px-5 font-semibold">
							Status
						</th>
						<th class="py-3 px-5 font-semibold">
							Joined
						</th>
						<th
							v-if="isOwner"
							class="py-3 px-5"
						/>
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-100">
					<tr
						v-for="m in members"
						:key="m.id"
						:class="m.is_active ? '' : 'opacity-50'"
					>
						<td class="py-3.5 px-5 font-medium text-slate-900">
							{{ m.email }}
							<span
								v-if="m.id === user?.id"
								class="ml-1 text-xs text-slate-400"
							>(you)</span>
						</td>
						<td class="py-3.5 px-5">
							<select
								v-if="isOwner && m.id !== user?.id"
								:value="m.role"
								class="rounded-lg border border-slate-300 px-2 py-1 text-sm bg-white outline-none focus:border-slate-800"
								@change="setRole(m, ($event.target as HTMLSelectElement).value)"
							>
								<option value="member">
									Member
								</option>
								<option value="owner">
									Owner
								</option>
							</select>
							<span
								v-else
								class="inline-flex rounded-full px-2.5 py-1 text-xs font-semibold"
								:class="m.role === 'owner' ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-100 text-slate-600'"
							>
								{{ m.role }}
							</span>
						</td>
						<td class="py-3.5 px-5">
							<span
								class="inline-flex rounded-full px-2.5 py-1 text-xs font-semibold"
								:class="m.is_active ? 'bg-green-100 text-green-700' : 'bg-slate-200 text-slate-500'"
							>
								{{ m.is_active ? "Active" : "Disabled" }}
							</span>
						</td>
						<td class="py-3.5 px-5 text-slate-500 text-sm">
							{{ new Date(m.created_at).toLocaleDateString() }}
						</td>
						<td
							v-if="isOwner"
							class="py-3.5 px-5 text-right whitespace-nowrap"
						>
							<button
								v-if="m.id !== user?.id"
								class="text-sm font-medium transition-colors"
								:class="m.is_active ? 'text-slate-500 hover:text-red-600' : 'text-slate-500 hover:text-green-600'"
								@click="setActive(m, !m.is_active)"
							>
								{{ m.is_active ? "Deactivate" : "Activate" }}
							</button>
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>

<script setup lang="ts">
import type { UserResponse } from "~/types/api";
import { useToastStore } from "~/stores/toast";

const api = useApi();
const { user, isOwner, fetchUser } = useAuth();
const toast = useToastStore();

// ensure we know our own role even on a hard refresh straight to /team
if (!user.value) await fetchUser();

const { data: members, refresh } = await useAsyncData(
	"org-members",
	() => api<UserResponse[]>("/org/members"),
);

const form = ref({ email: "", password: "", role: "member" });
const error = ref("");
const submitting = ref(false);

async function addMember() {
	error.value = "";
	submitting.value = true;
	try {
		await api("/org/members", {
			method: "POST",
			body: { email: form.value.email.trim(), password: form.value.password, role: form.value.role },
		});
		form.value = { email: "", password: "", role: "member" };
		toast.success("Member added.");
		await refresh();
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		error.value = typeof err.data?.detail === "string" ? err.data.detail : "Failed to add member";
		toast.error(error.value);
	}
	finally {
		submitting.value = false;
	}
}

async function patchMember(m: UserResponse, body: Record<string, unknown>) {
	try {
		await api(`/org/members/${m.id}`, { method: "PATCH", body });
		await refresh();
		toast.success("Member updated.");
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(typeof err.data?.detail === "string" ? err.data.detail : "Update failed");
	}
}

function setRole(m: UserResponse, role: string) {
	patchMember(m, { role });
}

function setActive(m: UserResponse, isActive: boolean) {
	patchMember(m, { is_active: isActive });
}
</script>
