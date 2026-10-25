# The payments image, built in two stages.
# Built from this folder:  docker build services/payments

# Stage 1: compile and package. Needs the full JDK and Maven.
FROM eclipse-temurin:21.0.12.1_1-jdk-noble AS build
WORKDIR /build

COPY mvnw pom.xml ./
COPY .mvn .mvn
COPY src src

# Tests run in CI and with `make test`, not during the image build.
# The cache mount keeps Maven's downloaded libraries between builds on this
# machine, without putting them in the image.
RUN --mount=type=cache,target=/root/.m2 ./mvnw -B -ntp package -DskipTests

# Stage 2: the image that runs. Only a Java runtime and the jar.
FROM eclipse-temurin:21.0.12.1_1-jre-noble

# Run as an ordinary user, not root
RUN useradd --system --no-create-home app
USER app

WORKDIR /app
COPY --from=build /build/target/payments-0.1.0.jar app.jar

EXPOSE 8080
# MaxRAMPercentage: let the heap use up to 60% of the container's memory limit
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=60", "-jar", "app.jar"]
