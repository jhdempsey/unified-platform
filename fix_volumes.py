with open('docker-compose.yml', 'r') as f:
    content = f.read()

# Find the networks section and add volumes: header
content = content.replace(
    '''networks:
  platform-network:
    driver: bridge

  kafka_data:''',
    '''networks:
  platform-network:
    driver: bridge

volumes:
  kafka_data:'''
)

with open('docker-compose.yml', 'w') as f:
    f.write(content)

print("✅ Fixed volumes section")
