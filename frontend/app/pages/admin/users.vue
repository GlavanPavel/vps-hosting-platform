<template>
	<div>
		<div class="mb-7">
			<h1 class="text-2xl font-bold text-slate-900">
				Users
			</h1>
			<p class="text-sm text-slate-500 mt-1">
				Every account across all organizations, with the resources each one runs.
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
							Organization
						</th>
						<th class="py-3 px-5 font-semibold">
							Role
						</th>
						<th class="py-3 px-5 font-semibold">
							Status
						</th>
						<th class="py-3 px-5 font-semibold text-right">
							Instances
						</th>
						<th class="py-3 px-5 font-semibold text-right">
							vCPUs
						</th>
						<th class="py-3 px-5 font-semibold text-right">
							RAM
						</th>
						<th class="py-3 px-5" />
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-100">
					<tr
						v-for="u in users ?? []"
						:key="u.id"
					>
						<td class="py-3.5 px-5 font-medium text-slate-900">
							{{ u.email }}
						</td>
						<td class="py-3.5 px-5 text-slate-600">
							{{ u.organization_name }}
						</td>
						<td class="py-3.5 px-5">
							<span
								class="text-xs font-semibold rounded-full px-2.5 py-1"
								:class="roleTone(u.role)"
							>
								{{ u.role }}
							</span>
						</td>
						<td class="py-3.5 px-5">
							<span
								v-if="u.is_active"
								class="text-xs font-medium text-emerald-700"
							>Active</span>
							<span
								v-else
								class="text-xs font-medium text-slate-400"
							>Disabled</span>
						</td>
						<td class="py-3.5 px-5 text-right text-slate-600 tabular-nums">
							{{ u.instances }}
						</td>
						<td class="py-3.5 px-5 text-right text-slate-600 tabular-nums">
							{{ u.vcpus_allocated }}
						</td>
						<td class="py-3.5 px-5 text-right text-slate-600 tabular-nums">
							{{ u.ram_gb_allocated.toFixed(1) }} GB
						</td>
						<td class="py-3.5 px-5 text-right whitespace-nowrap">
							<template v-if="u.id !== self?.id">
								<button
									class="text-sm font-medium mr-4 transition-colors"
									:class="u.is_active ? 'text-slate-500 hover:text-amber-600' : 'text-slate-500 hover:text-emerald-600'"
									@click="setActive(u, !u.is_active)"
								>
									{{ u.is_active ? "Deactivate" : "Reactivate" }}
								</button>
								<button
									class="text-sm font-medium text-slate-400 hover:text-red-600 transition-colors"
									@click="remove(u)"
								>
									Delete
								</button>
							</template>
							<span
								v-else
								class="text-xs text-slate-300"
							>you</span>
						</td>
					</tr>
					<tr v-if="(users?.length ?? 0) === 0">
						<td
							colspan="8"
							class="py-6 px-5 text-center text-sm text-slate-400"
						>
							No users yet.
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>

<script setup lang="ts">
import type { AdminUserRow } from "~/types/api";
import { useToastStore } from "~/stores/toast";

definePageMeta({ layout: "admin", middleware: "admin" });

const api = useApi();
const toast = useToastStore();
const { user: self } = useAuth();
const { data: users, refresh } = await useAsyncData(
	"admin-users",
	() => api<AdminUserRow[]>("/admin/users"),
);

function roleTone(role: string): string {
	if (role === "admin") return "bg-indigo-100 text-indigo-700";
	if (role === "owner") return "bg-slate-800 text-white";
	return "bg-slate-100 text-slate-600";
}

async function setActive(u: AdminUserRow, makeActive: boolean) {
	if (!makeActive && !confirm(`Deactivate ${u.email}? This blocks their login and stops the instances they own.`)) return;
	try {
		await api(`/admin/users/${u.id}`, { method: "PATCH", body: { is_active: makeActive } });
		toast.success(makeActive ? `Reactivated ${u.email}.` : `Deactivated ${u.email}.`);
		await refresh();
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(err.data?.detail ?? "Action failed");
	}
}

async function remove(u: AdminUserRow) {
	if (!confirm(`Delete ${u.email}? Their instances stay (reassigned to the org); their SSH keys are removed. This cannot be undone.`)) return;
	try {
		await api(`/admin/users/${u.id}`, { method: "DELETE" });
		toast.success(`Deleted ${u.email}.`);
		await refresh();
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(err.data?.detail ?? "Could not delete user");
	}
}
</script>
