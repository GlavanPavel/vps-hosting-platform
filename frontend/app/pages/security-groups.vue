<template>
	<div>
		<div class="mb-7">
			<h1 class="text-2xl font-bold text-slate-900">
				Security Groups
			</h1>
			<p class="text-sm text-slate-500 mt-1">
				Firewall rule sets you can attach to instances.
			</p>
		</div>

		<div class="bg-white rounded-xl shadow-sm border border-slate-200/70 p-6 mb-8">
			<h2 class="font-semibold text-slate-900 mb-4">
				Create a security group
			</h2>
			<form
				class="space-y-4"
				@submit.prevent="submit"
			>
				<div class="grid grid-cols-2 gap-6">
					<div class="flex flex-col gap-2">
						<label class="text-sm font-medium text-slate-700">Name</label>
						<input
							v-model="form.name"
							type="text"
							required
							placeholder="allow-ssh"
							class="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
						>
					</div>
					<div class="flex flex-col gap-2">
						<label class="text-sm font-medium text-slate-700">Description</label>
						<input
							v-model="form.description"
							type="text"
							placeholder="Optional"
							class="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
						>
					</div>
				</div>

				<div class="space-y-2">
					<label class="text-sm font-medium text-slate-700">Rules</label>
					<div
						v-for="(rule, i) in form.rules"
						:key="i"
						class="flex gap-3 items-center"
					>
						<select
							v-model="rule.direction"
							class="rounded-lg border border-slate-300 px-3 py-2.5 bg-white outline-none focus:border-slate-800 transition"
						>
							<option value="ingress">
								ingress
							</option>
							<option value="egress">
								egress
							</option>
						</select>
						<select
							v-model="rule.protocol"
							class="rounded-lg border border-slate-300 px-3 py-2.5 bg-white outline-none focus:border-slate-800 transition"
						>
							<option :value="null">
								any
							</option>
							<option value="tcp">
								tcp
							</option>
							<option value="udp">
								udp
							</option>
							<option value="icmp">
								icmp
							</option>
						</select>
						<input
							v-model.number="rule.port_range_min"
							type="number"
							min="1"
							max="65535"
							placeholder="port from"
							class="w-28 rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 transition"
						>
						<input
							v-model.number="rule.port_range_max"
							type="number"
							min="1"
							max="65535"
							placeholder="port to"
							class="w-28 rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 transition"
						>
						<input
							v-model="rule.remote_ip_prefix"
							type="text"
							placeholder="0.0.0.0/0"
							class="w-40 rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 transition font-mono text-sm"
						>
						<button
							v-if="form.rules.length > 1"
							type="button"
							class="text-slate-400 hover:text-red-500 transition-colors"
							@click="form.rules.splice(i, 1)"
						>
							<Icon
								name="solar:close-circle-outline"
								class="text-xl"
							/>
						</button>
					</div>
					<button
						type="button"
						class="text-sm text-slate-600 hover:text-slate-900 font-medium transition-colors"
						@click="addRule"
					>
						+ Add another rule
					</button>
				</div>

				<p
					v-if="error"
					class="text-red-600 text-sm"
				>
					{{ error }}
				</p>
				<button
					type="submit"
					:disabled="submitting"
					class="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-60 text-white font-medium py-2.5 px-5 rounded-lg transition-colors"
				>
					<Icon
						name="solar:shield-plus-outline"
						class="text-lg"
					/>
					{{ submitting ? "Creating…" : "Create security group" }}
				</button>
			</form>
		</div>

		<EmptyState
			v-if="!securityGroups || securityGroups.length === 0"
			icon="solar:shield-keyhole-outline"
			title="No security groups yet"
			description="Create a rule set — at minimum, allow inbound SSH on port 22."
		/>

		<div
			v-else
			class="space-y-4"
		>
			<div
				v-for="sg in securityGroups"
				:key="sg.id"
				class="bg-white rounded-xl shadow-sm border border-slate-200/70 p-6"
			>
				<div class="flex items-center justify-between mb-3">
					<div class="flex items-center gap-3">
						<h3 class="font-bold text-lg text-slate-900">
							{{ sg.name }}
						</h3>
						<SyncBadge :synced="!!sg.openstack_id" />
					</div>
					<button
						v-if="can('security_group:delete')"
						class="text-slate-400 hover:text-red-600 transition-colors"
						title="Delete security group"
						@click="remove(sg)"
					>
						<Icon
							name="solar:trash-bin-trash-outline"
							class="text-xl"
						/>
					</button>
				</div>
				<p
					v-if="sg.description"
					class="text-slate-500 text-sm mb-3"
				>
					{{ sg.description }}
				</p>
				<table
					v-if="sg.rules.length > 0"
					class="w-full text-left text-sm"
				>
					<thead class="text-slate-400 text-xs uppercase tracking-wider">
						<tr>
							<th class="py-1.5 pr-4 font-semibold">
								Direction
							</th>
							<th class="py-1.5 pr-4 font-semibold">
								Protocol
							</th>
							<th class="py-1.5 pr-4 font-semibold">
								Ports
							</th>
							<th class="py-1.5 pr-4 font-semibold">
								Source
							</th>
						</tr>
					</thead>
					<tbody>
						<tr
							v-for="rule in sg.rules"
							:key="rule.id"
							class="text-slate-600"
						>
							<td class="py-1.5 pr-4">
								{{ rule.direction }}
							</td>
							<td class="py-1.5 pr-4">
								{{ rule.protocol ?? "any" }}
							</td>
							<td class="py-1.5 pr-4">
								{{ rule.port_range_min === null ? "all" : rule.port_range_min === rule.port_range_max ? rule.port_range_min : `${rule.port_range_min}–${rule.port_range_max}` }}
							</td>
							<td class="py-1.5 pr-4 font-mono">
								{{ rule.remote_ip_prefix ?? "any" }}
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import type { SecurityGroupResponse } from "~/types/api";
import { useToastStore } from "~/stores/toast";

const api = useApi();
const { can } = useAuth();
const toast = useToastStore();

const { data: securityGroups, refresh } = await useAsyncData(
	"security-groups",
	() => api<SecurityGroupResponse[]>("/security-groups/"),
);

interface RuleForm {
	direction: "ingress" | "egress";
	protocol: "tcp" | "udp" | "icmp" | null;
	port_range_min: number | null;
	port_range_max: number | null;
	remote_ip_prefix: string;
}

function emptyRule(): RuleForm {
	return { direction: "ingress", protocol: "tcp", port_range_min: null, port_range_max: null, remote_ip_prefix: "0.0.0.0/0" };
}

const form = ref({
	name: "",
	description: "",
	rules: [emptyRule()],
});
const error = ref("");
const submitting = ref(false);

function addRule() {
	form.value.rules.push(emptyRule());
}

async function submit() {
	error.value = "";
	submitting.value = true;
	try {
		await api("/security-groups/", {
			method: "POST",
			body: {
				name: form.value.name.trim(),
				description: form.value.description.trim() || null,
				rules: form.value.rules.map(r => ({
					direction: r.direction,
					protocol: r.protocol,
					port_range_min: r.port_range_min || null,
					// a single port shorthand: missing max falls back to min
					port_range_max: r.port_range_max || r.port_range_min || null,
					remote_ip_prefix: r.remote_ip_prefix.trim() || null,
				})),
			},
		});
		form.value = { name: "", description: "", rules: [emptyRule()] };
		toast.success("Security group created — syncing…");
		await refresh();
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		error.value = typeof err.data?.detail === "string" ? err.data.detail : "Failed to create security group";
		toast.error(error.value);
	}
	finally {
		submitting.value = false;
	}
}

async function remove(sg: SecurityGroupResponse) {
	if (!confirm(`Delete security group "${sg.name}"?`)) return;
	try {
		await api(`/security-groups/${sg.id}`, { method: "DELETE" });
		await refresh();
		toast.success(`Deleting security group "${sg.name}"…`);
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(err.data?.detail ?? "Failed to delete security group");
	}
}

// poll so the Synced badge updates once Celery mirrors the group
let poll: ReturnType<typeof setInterval> | undefined;
onMounted(() => {
	poll = setInterval(refresh, 5000);
});
onUnmounted(() => clearInterval(poll));
</script>
