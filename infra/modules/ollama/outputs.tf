output "private_ip" {
  value = aws_instance.ollama.private_ip
}

output "private_dns_name" {
  value = try(aws_route53_record.ollama[0].fqdn, null)
}

output "base_url" {
  value = var.enable_private_dns ? "http://ollama.ai-platform.internal:11434" : "http://${aws_instance.ollama.private_ip}:11434"
}
output "security_group_id" {
  value = aws_security_group.ollama.id
}

output "cloudwatch_log_group" {
  value = aws_cloudwatch_log_group.ollama.name
}
