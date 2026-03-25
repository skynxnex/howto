# Benchmark Results — 2026-03-25 14:05

## Prompt
```kotlin
You are working in an existing Kotlin Spring Boot service. Here is the relevant code:

```kotlin
// Existing domain types
data class Offer(val id: Long, val dealerId: Long, val vehicleId: Long, val status: OfferStatus)
enum class OfferStatus { ACTIVE, SOLD, REMOVED }
data class SyncResult(val synced: Int, val failed: List<Long>, val skipped: Int)

// Existing repository — use these methods, do not modify
@Repository
class OfferRepository(private val jdbcTemplate: NamedParameterJdbcTemplate) {
    fun findByDealerId(dealerId: Long): List<Offer> { ... }
    fun findById(id: Long): Offer? { ... }
    fun updateStatus(id: Long, status: OfferStatus): Boolean { ... }
    fun bulkUpdateStatus(ids: List<Long>, status: OfferStatus): Int { ... }
}

// Existing external client — use as-is
@Component
class VehicleApiClient {
    fun fetchActiveVehicleIds(dealerId: Long): Set<Long>   // throws VehicleApiException on failure
    fun isVehicleSold(vehicleId: Long): Boolean            // throws VehicleApiException on failure
}

// Existing exception types
class VehicleApiException(message: String, cause: Throwable? = null) : RuntimeException(message, cause)
class SyncException(message: String, cause: Throwable? = null) : RuntimeException(message, cause)
```

Implement a `syncDealerOffers(dealerId: Long): SyncResult` method for the following service class:

```kotlin
@Service
class OfferSyncService(
    private val offerRepository: OfferRepository,
    private val vehicleApiClient: VehicleApiClient,
    private val logger: Logger = LoggerFactory.getLogger(OfferSyncService::class.java)
) {
    // implement here
}
```

Requirements:
1. Fetch current offers for the dealer from the repository
2. Fetch active vehicle IDs from the external API — if this call fails, throw SyncException
3. For each ACTIVE offer:
   - If its vehicleId is NOT in the active set, check if the vehicle is sold via the API
   - If sold → mark offer as SOLD; if not → mark as REMOVED
   - If the API call for a single vehicle fails, log a warning and add the offer ID to `failed` — do not abort the whole sync
4. Offers already SOLD or REMOVED → count as skipped, do not touch them
5. Use bulkUpdateStatus where possible to minimize DB calls
6. Return a SyncResult with counts
7. No explanation, just the method
```

## Speed Summary

| | Time to first token | Total time | Output tokens |
|---|---|---|---|
| Claude Sonnet 4.6 (Vertex AI) | 2555 ms | 7835 ms | ~535 |
| qwen3:14b         (think=off) | 95548 ms | 119633 ms | ~286 |
| qwen2.5-coder:14b (think=off) | 126659 ms | 164525 ms | ~338 |
| phi4:14b          (think=off) | 58897 ms | 90916 ms | ~374 |
| gemma3:12b        (think=off) | 955 ms | 52164 ms | ~549 |
| mistral-nemo:12b  (think=off) | ERROR | ERROR | — |

---

## Claude Sonnet 4.6 (Vertex AI)

```kotlin
```kotlin
fun syncDealerOffers(dealerId: Long): SyncResult {
    val currentOffers = offerRepository.findByDealerId(dealerId)

    val activeVehicleIds = try {
        vehicleApiClient.fetchActiveVehicleIds(dealerId)
    } catch (e: VehicleApiException) {
        throw SyncException("Failed to fetch active vehicle IDs for dealer $dealerId", e)
    }

    val activeOffers = currentOffers.filter { it.status == OfferStatus.ACTIVE }
    val skipped = currentOffers.size - activeOffers.size

    val offersNeedingStatusCheck = activeOffers.filter { it.vehicleId !in activeVehicleIds }
    val offersStillActive = activeOffers.filter { it.vehicleId in activeVehicleIds }

    val toMarkSold = mutableListOf<Long>()
    val toMarkRemoved = mutableListOf<Long>()
    val failed = mutableListOf<Long>()

    for (offer in offersNeedingStatusCheck) {
        try {
            val sold = vehicleApiClient.isVehicleSold(offer.vehicleId)
            if (sold) {
                toMarkSold.add(offer.id)
            } else {
                toMarkRemoved.add(offer.id)
            }
        } catch (e: VehicleApiException) {
            logger.warn("Failed to check sold status for vehicle ${offer.vehicleId} (offer ${offer.id}): ${e.message}")
            failed.add(offer.id)
        }
    }

    var syncedCount = 0

    if (toMarkSold.isNotEmpty()) {
        syncedCount += offerRepository.bulkUpdateStatus(toMarkSold, OfferStatus.SOLD)
    }

    if (toMarkRemoved.isNotEmpty()) {
        syncedCount += offerRepository.bulkUpdateStatus(toMarkRemoved, OfferStatus.REMOVED)
    }

    return SyncResult(
        synced = syncedCount,
        failed = failed,
        skipped = skipped
    )
}
```
```

## qwen3:14b         (think=off)

```kotlin
```kotlin
fun syncDealerOffers(dealerId: Long): SyncResult {
    val offers = offerRepository.findByDealerId(dealerId)
    val activeVehicleIds: Set<Long> = try {
        vehicleApiClient.fetchActiveVehicleIds(dealerId)
    } catch (e: VehicleApiException) {
        throw SyncException("Failed to fetch active vehicle IDs for dealer $dealerId", e)
    }

    val toUpdate: MutableList<Long> = mutableListOf()
    val failed: MutableList<Long> = mutableListOf()
    var skipped = 0

    offers.forEach { offer ->
        if (offer.status != OfferStatus.ACTIVE) {
            skipped++
            return@forEach
        }

        if (offer.vehicleId !in activeVehicleIds) {
            try {
                val isSold = vehicleApiClient.isVehicleSold(offer.vehicleId)
                if (isSold) {
                    toUpdate.add(offer.id)
                } else {
                    toUpdate.add(offer.id)
                }
            } catch (e: VehicleApiException) {
                logger.warn("Failed to check vehicle status for vehicle ID ${offer.vehicleId}: ${e.message}", e)
                failed.add(offer.id)
            }
        }
    }

    if (toUpdate.isNotEmpty()) {
        offerRepository.bulkUpdateStatus(toUpdate, OfferStatus.SOLD)
    }

    return SyncResult(toUpdate.size, failed, skipped)
}
```
```

## qwen2.5-coder:14b (think=off)

```kotlin
```kotlin
@Service
class OfferSyncService(
    private val offerRepository: OfferRepository,
    private val vehicleApiClient: VehicleApiClient,
    private val logger: Logger = LoggerFactory.getLogger(OfferSyncService::class.java)
) {
    fun syncDealerOffers(dealerId: Long): SyncResult {
        val offers = offerRepository.findByDealerId(dealerId)
        val activeVehicleIds: Set<Long>
        
        try {
            activeVehicleIds = vehicleApiClient.fetchActiveVehicleIds(dealerId)
        } catch (e: VehicleApiException) {
            throw SyncException("Failed to fetch active vehicle IDs", e)
        }

        val updates = mutableListOf<Pair<Long, OfferStatus>>()
        val failed = mutableListOf<Long>()
        var skipped = 0

        for (offer in offers) {
            when (offer.status) {
                OfferStatus.SOLD, OfferStatus.REMOVED -> skipped++
                else -> {
                    if (!activeVehicleIds.contains(offer.vehicleId)) {
                        try {
                            val isSold = vehicleApiClient.isVehicleSold(offer.vehicleId)
                            updates.add(offer.id to if (isSold) OfferStatus.SOLD else OfferStatus.REMOVED)
                        } catch (e: VehicleApiException) {
                            logger.warn("Failed to check vehicle status for offer ID ${offer.id}: ${e.message}")
                            failed.add(offer.id)
                        }
                    }
                }
            }
        }

        val bulkUpdateResult = offerRepository.bulkUpdateStatus(updates.map { it.first }, updates.map { it.second })
        val synced = updates.size - failed.size

        return SyncResult(synced, failed, skipped)
    }
}
```
```

## phi4:14b          (think=off)

```kotlin
```kotlin
@Service
class OfferSyncService(
    private val offerRepository: OfferRepository,
    private val vehicleApiClient: VehicleApiClient,
    private val logger: Logger = LoggerFactory.getLogger(OfferSyncService::class.java)
) {
    
    fun syncDealerOffers(dealerId: Long): SyncResult {
        val offers = offerRepository.findByDealerId(dealerId)
        val activeVehicleIds = try {
            vehicleApiClient.fetchActiveVehicleIds(dealerId)
        } catch (e: VehicleApiException) {
            throw SyncException("Failed to fetch active vehicle IDs for dealer $dealerId", e)
        }
        
        val idsToMarkSold = mutableListOf<Long>()
        val idsToRemove = mutableListOf<Long>()
        val failedIds = mutableListOf<Long>()

        offers.filter { it.status == OfferStatus.ACTIVE }.forEach { offer ->
            if (offer.vehicleId !in activeVehicleIds) {
                try {
                    if (vehicleApiClient.isVehicleSold(offer.vehicleId)) {
                        idsToMarkSold.add(offer.id)
                    } else {
                        idsToRemove.add(offer.id)
                    }
                } catch (e: VehicleApiException) {
                    logger.warn("Failed to check vehicle status for offer ID ${offer.id}", e)
                    failedIds.add(offer.id)
                }
            }
        }

        if (idsToMarkSold.isNotEmpty()) {
            offerRepository.bulkUpdateStatus(idsToMarkSold, OfferStatus.SOLD)
        }
        if (idsToRemove.isNotEmpty()) {
            offerRepository.bulkUpdateStatus(idsToRemove, OfferStatus.REMOVED)
        }

        val skippedCount = offers.count { it.status == OfferStatus.SOLD || it.status == OfferStatus.REMOVED }

        return SyncResult(synced = idsToMarkSold.size + idsToRemove.size, failed = failedIds, skipped = skippedCount)
    }
}
```
```

## gemma3:12b        (think=off)

```kotlin
```kotlin
@Service
class OfferSyncService(
    private val offerRepository: OfferRepository,
    private val vehicleApiClient: VehicleApiClient,
    private val logger: Logger = LoggerFactory.getLogger(OfferSyncService::class.java)
) {
    fun syncDealerOffers(dealerId: Long): SyncResult {
        val offers = offerRepository.findByDealerId(dealerId)
        try {
            val activeVehicleIds = vehicleApiClient.fetchActiveVehicleIds(dealerId)
        } catch (e: VehicleApiException) {
            throw SyncException("Failed to fetch active vehicle IDs for dealer $dealerId", e)
        }

        var synced = 0
        var failed = mutableListOf<Long>()
        var skipped = 0
        val updatedOfferIds = mutableListOf<Long>()

        for (offer in offers) {
            when (offer.status) {
                OfferStatus.ACTIVE -> {
                    if (activeVehicleIds.contains(offer.vehicleId)) {
                        synced++
                    } else {
                        try {
                            if (vehicleApiClient.isVehicleSold(offer.vehicleId)) {
                                offerRepository.updateStatus(offer.id, OfferStatus.SOLD)
                                synced++
                            } else {
                                offerRepository.updateStatus(offer.id, OfferStatus.REMOVED)
                                synced++
                            }
                        } catch (e: VehicleApiException) {
                            logger.warn("Failed to check vehicle status for offer ${offer.id}: ${e.message}")
                            failed.add(offer.id)
                        }
                    }
                    updatedOfferIds.add(offer.id)
                }
                OfferStatus.SOLD -> skipped++
                OfferStatus.REMOVED -> skipped++
            }
        }

        if (updatedOfferIds.isNotEmpty()) {
            val statuses = updatedOfferIds.groupBy { offerRepository.findById(it)?.status }
            statuses.forEach { (status, ids) ->
                when (status) {
                    OfferStatus.SOLD -> {
                        val updatedCount = offerRepository.bulkUpdateStatus(ids, OfferStatus.SOLD)
                        synced += updatedCount
                    }
                    OfferStatus.REMOVED -> {
                        val updatedCount = offerRepository.bulkUpdateStatus(ids, OfferStatus.REMOVED)
                        synced += updatedCount
                    }
                }
            }
        }

        return SyncResult(synced, failed, skipped)
    }
}
```
```

## mistral-nemo:12b  (think=off)

**Error:** HTTP Error 500: Internal Server Error

