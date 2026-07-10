export interface UserResponse {
	id: number;
	email: string;
	organization_id: number;
	role: string;
	is_active: boolean;
	created_at: string;
	// derived from role on the backend; used to gate UI controls
	permissions?: string[];
}

export interface InstanceResponse {
	id: number;
	name: string;
	status: string;
	flavor_name: string;
	image_name: string;
	private_ip_address: string | null;
	created_at: string;
}

export interface KeypairResponse {
	id: number;
	name: string;
	fingerprint: string;
	openstack_name: string | null;
	created_at: string;
}

export interface SubnetResponse {
	id: number;
	name: string;
	cidr: string;
	openstack_subnet_id: string | null;
	created_at: string;
}

export interface NetworkResponse {
	id: number;
	name: string;
	openstack_network_id: string | null;
	subnets: SubnetResponse[];
	created_at: string;
}

export interface SecurityGroupRuleResponse {
	id: number;
	direction: string;
	protocol: string | null;
	port_range_min: number | null;
	port_range_max: number | null;
	remote_ip_prefix: string | null;
}

export interface SecurityGroupResponse {
	id: number;
	name: string;
	description: string | null;
	openstack_id: string | null;
	rules: SecurityGroupRuleResponse[];
	created_at: string;
}

export interface FloatingIPResponse {
	id: number;
	ip_address: string;
	openstack_floatingip_id: string;
	external_network_name: string;
	status: string;
	instance_id: number | null;
	instance_name: string | null;
	created_at: string;
}

export interface KeypairGenerateResponse extends KeypairResponse {
	// returned exactly once, right after generation — never persisted server-side
	private_key: string;
}

export interface KeypairBrief {
	id: number;
	name: string;
}

export interface SubnetBrief {
	id: number;
	name: string;
	cidr: string;
	network_name: string;
}

export interface SecurityGroupBrief {
	id: number;
	name: string;
}

export interface FloatingIPBrief {
	ip_address: string;
	status: string;
}

export interface VolumeBrief {
	id: number;
	name: string;
	size_gb: number;
	status: string;
	device: string | null;
}

export interface InstanceDetailResponse {
	id: number;
	name: string;
	status: string;
	flavor_name: string;
	image_name: string;
	vcpus: number;
	ram_mb: number;
	disk_gb: number;
	private_ip_address: string | null;
	openstack_id: string | null;
	created_at: string;
	keypair: KeypairBrief | null;
	subnet: SubnetBrief | null;
	security_groups: SecurityGroupBrief[];
	floating_ip: FloatingIPBrief | null;
	volumes: VolumeBrief[];
}

export interface MetricPoint {
	timestamp: string;
	cpu_time: number;
	ram_mb: number;
}

export interface MetricsResponse {
	instance_id: string;
	data: MetricPoint[];
}

export interface ConsoleResponse {
	console_url: string;
}

export interface ConsoleLogResponse {
	output: string;
}

export interface InstanceEventResponse {
	id: number;
	severity: string; // info | warning | error
	message: string;
	created_at: string;
}

export interface VolumeResponse {
	id: number;
	name: string;
	size_gb: number;
	status: string;
	openstack_volume_id: string | null;
	instance_id: number | null;
	device: string | null;
	created_at: string;
}

export interface InstanceUsage {
	id: number;
	name: string;
	flavor_name: string;
	status: string;
	hours: number;
}

export interface VolumeUsage {
	id: number;
	name: string;
	size_gb: number;
}

export interface UsageResponse {
	instances: InstanceUsage[];
	volumes: VolumeUsage[];
	running_instances: number;
	vcpus_allocated: number;
	ram_gb_allocated: number;
	storage_gb: number;
}

// ── quotas ────────────────────────────────────────────────────────────────────

export interface QuotaLimits {
	max_instances: number;
	max_vcpus: number;
	max_ram_gb: number;
	max_volumes: number;
	max_storage_gb: number;
	max_floating_ips: number;
}

export interface QuotaUsage {
	instances: number;
	vcpus: number;
	ram_gb: number;
	volumes: number;
	storage_gb: number;
	floating_ips: number;
}

export interface QuotaResponse {
	limits: QuotaLimits;
	usage: QuotaUsage;
	is_default: boolean;
}

// ── admin (platform-level, cross-org) ─────────────────────────────────────────

export interface CloudCapacity {
	hypervisor_count: number;
	vcpus_total: number;
	vcpus_used: number;
	ram_gb_total: number;
	ram_gb_used: number;
	disk_gb_total: number;
	disk_gb_used: number;
	running_vms: number;
	storage_gb_total: number | null;
	storage_gb_used: number | null;
	updated_at: string;
}

export interface PlatformTotals {
	organizations: number;
	users: number;
	instances: number;
	running_instances: number;
	volumes: number;
	vcpus_allocated: number;
	ram_gb_allocated: number;
	storage_gb: number;
}

export interface AdminOverview {
	capacity: CloudCapacity | null;
	totals: PlatformTotals;
}

export interface OrgUsageRow {
	id: number;
	name: string;
	users: number;
	instances: number;
	running_instances: number;
	vcpus_allocated: number;
	ram_gb_allocated: number;
	storage_gb: number;
	suspended: boolean;
	created_at: string;
}

export interface AdminUserRow {
	id: number;
	email: string;
	role: string;
	is_active: boolean;
	organization_id: number;
	organization_name: string;
	instances: number;
	vcpus_allocated: number;
	ram_gb_allocated: number;
	created_at: string;
}

export interface ImageResponse {
	id: number;
	name: string;
	source_type: string;
	source_url: string | null;
	source_instance_id: number | null;
	disk_format: string;
	openstack_image_id: string | null;
	status: string;
	size_bytes: number | null;
	min_disk_gb: number | null;
	is_public: boolean;
	created_at: string;
}
