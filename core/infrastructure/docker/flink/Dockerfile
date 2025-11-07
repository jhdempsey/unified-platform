FROM flink:1.18-scala_2.12-java11

# Install build dependencies and full JDK
RUN apt-get update && \
    apt-get install -y \
        python3 \
        python3-pip \
        python3-dev \
        openjdk-11-jdk-headless \
        build-essential \
        wget && \
    rm -rf /var/lib/apt/lists/*

# The base image has JRE at /opt/java/openjdk, but we need JDK for building
# apt installs JDK to /usr/lib/jvm/ - find it dynamically
RUN JAVA_HOME=$(find /usr/lib/jvm -name "java-11-openjdk-*" -type d | head -1) && \
    echo "Found JAVA_HOME: $JAVA_HOME" && \
    echo "export JAVA_HOME=$JAVA_HOME" >> /etc/environment && \
    ln -sf $JAVA_HOME/bin/java /usr/bin/java

# Install Flink connectors
RUN wget -P /opt/flink/lib/ \
    https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.0.2-1.18/flink-sql-connector-kafka-3.0.2-1.18.jar && \
    wget -P /opt/flink/lib/ \
    https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-avro-confluent-registry/1.18.0/flink-sql-avro-confluent-registry-1.18.0.jar && \
    wget -P /opt/flink/lib/ \
    https://repo.maven.apache.org/maven2/org/apache/flink/flink-json/1.18.0/flink-json-1.18.0.jar

# Install PyFlink with proper JAVA_HOME pointing to the apt-installed JDK
RUN JAVA_HOME=$(find /usr/lib/jvm -name "java-11-openjdk-*" -type d | head -1) && \
    export JAVA_HOME && \
    echo "Building PyFlink with JAVA_HOME=$JAVA_HOME" && \
    pip3 install --no-cache-dir \
        apache-flink==1.18.0 \
        kafka-python \
        confluent-kafka \
        avro-python3

# Set JAVA_HOME for runtime
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH="${JAVA_HOME}/bin:${PATH}"

WORKDIR /opt/flink
